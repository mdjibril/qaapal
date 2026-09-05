import streamlit as st

import database as db
from ai_utils import validate_and_generate
from file_utils import export_instructor_guide_to_word, export_student_workbook_to_word
from workbook_utils import (
    build_workbook_prompt,
    normalize_nos,
    split_workbook_records,
    validate_workbook_items,
)


def _generation_blocked(role, tier, credits, using_byok, policy):
    if role == "admin":
        return False
    if tier == "free":
        return True
    quota = policy.get("platform_quota")
    if using_byok or quota is None:
        return False
    if quota == 0:
        return True
    return (st.session_state.get("ai_quota_used", 0) or 0) >= quota


def main():
    st.title("📚 NOS Workbook Generator")
    st.info("Generate a Student Workbook and matching Instructor Guide from the selected sidebar NOS.")

    role = st.session_state.get("user_role", "assessor")
    tier = st.session_state.get("subscription_tier", "free")
    is_superadmin = role == "admin"
    if role != "admin" and tier not in ("platform_pass", "lifetime", "enterprise"):
        st.error("Workbook generation is available on Platform Pass, Lifetime, and Enterprise plans.")
        return

    trade_id = st.session_state.get("selected_trade_id")
    trade_level_id = st.session_state.get("selected_trade_level_id")
    trade_name = st.session_state.get("selected_trade_name", "Selected Trade")
    level_name = st.session_state.get("selected_trade_level_name", "Selected Level")
    if not trade_id or not trade_level_id:
        st.warning("Please select a trade and level in the sidebar first.")
        return

    nos_data = db.fetch_nested_nos(trade_id=trade_id, trade_level_id=trade_level_id)
    records = normalize_nos(nos_data)
    selection_fingerprint = (trade_id, trade_level_id)
    if st.session_state.get("workbook_selection_fingerprint") != selection_fingerprint:
        for key in (
            "workbook_items",
            "workbook_student_name",
            "workbook_trade_name",
            "workbook_level_name",
        ):
            st.session_state.pop(key, None)
        st.session_state.workbook_selection_fingerprint = selection_fingerprint
    unit_count = len({record["unit_code"] for record in records})
    st.write(f"**Trade:** {trade_name}  |  **Level:** {level_name}")
    st.write(f"**Units:** {unit_count}  |  **Performance Criteria:** {len(records)}")
    if not records:
        st.warning("No performance criteria were found for the selected trade and level.")
        return

    student_name = st.text_input("Student Name", placeholder="Enter the student name")
    user_id = st.session_state.user_session.id
    role = st.session_state.get("user_role", "assessor")
    tier = st.session_state.get("subscription_tier", "free")
    using_byok = st.session_state.get("using_byok", False)
    policy = st.session_state.get("_ai_policy", {})
    previous_workbooks = db.list_workbooks(user_id, admin=is_superadmin)
    matching_workbooks = [
        workbook for workbook in previous_workbooks
        if workbook.get("trade_id") == trade_id
        and workbook.get("trade_level_id") == trade_level_id
    ]
    duplicate_workbook = matching_workbooks[0] if matching_workbooks else None
    duplicate_blocked = duplicate_workbook is not None and not is_superadmin
    blocked = _generation_blocked(
        role,
        tier,
        st.session_state.get("credits_balance", 0),
        using_byok,
        policy,
    )
    if st.button(
        "Generate Workbook and Instructor Guide",
        type="primary",
        disabled=blocked or duplicate_blocked,
    ):
        if not student_name.strip():
            st.error("Please enter the student name first.")
            return

        provider = st.session_state.get("ai_provider")
        keys = st.session_state.get("target_keys", [])
        model = st.session_state.get("target_model")
        if not keys:
            st.warning(f"Please enter the {provider} API key(s) in the sidebar.")
            return

        with st.status("Preparing workbook...", expanded=True) as status:
            source = "your BYOK" if using_byok else "the internal platform key"
            st.write(f"🔑 Using {source}.")
            batches = split_workbook_records(records)
            items = []
            for batch_number, batch_records in enumerate(batches, start=1):
                st.write(f"🧾 Generating batch {batch_number} of {len(batches)} ({len(batch_records)} PCs)...")
                response = validate_and_generate(
                    provider=provider,
                    model_name=model,
                    api_keys=keys,
                    prompt=build_workbook_prompt(trade_name, level_name, batch_records),
                    system_prompt="Return only the requested JSON assessment-item list for this batch.",
                )
                if "API_ERROR" in str(response):
                    st.error(f"Workbook batch {batch_number} failed: {response}")
                    return
                try:
                    items.extend(validate_workbook_items(response, batch_records))
                except ValueError as exc:
                    st.error(f"Workbook batch {batch_number} validation failed: {exc}")
                    return

            if role != "admin":
                allowed, reason = db.consume_ai_credit(
                    st.session_state.org_id,
                    tier,
                    using_byok,
                )
                if not allowed:
                    st.error(f"Generation allowance unavailable: {reason}")
                    return
                if reason == "free_credit":
                    st.session_state.credits_balance -= 1
                elif reason == "platform_quota":
                    st.session_state.ai_quota_used = st.session_state.get("ai_quota_used", 0) + 1

            st.session_state.workbook_items = items
            st.session_state.workbook_student_name = student_name.strip()
            st.session_state.workbook_trade_name = trade_name
            st.session_state.workbook_level_name = level_name
            st.session_state.workbook_selection_fingerprint = selection_fingerprint
            saved, save_result = db.save_workbook(
                org_id=st.session_state.get("org_id"),
                created_by=user_id,
                trade_id=trade_id,
                trade_level_id=trade_level_id,
                trade_name=trade_name,
                level_name=level_name,
                student_name=student_name.strip(),
                assessment_items=items,
            )
            if saved:
                st.session_state.workbook_id = save_result.get("id")
            else:
                st.warning(f"Workbook generated but could not be saved: {save_result}")
            status.update(label="✅ Workbook package ready", state="complete", expanded=False)

    st.markdown("### Previous Workbooks")
    if duplicate_workbook:
        if is_superadmin:
            st.info("A workbook already exists for this trade and level. You may regenerate it as Super Admin.")
        else:
            st.warning(
                "A workbook already exists for this trade and level. "
                "Download the previous workbook below before generating another one."
            )
        existing_workbook = db.fetch_workbook(duplicate_workbook["id"], user_id, admin=is_superadmin)
        if existing_workbook and existing_workbook.get("assessment_items"):
            existing_items = existing_workbook["assessment_items"]
            existing_student_doc = export_student_workbook_to_word(
                existing_workbook["trade_name"], existing_workbook["level_name"],
                existing_workbook["student_name"], existing_items,
            )
            existing_instructor_doc = export_instructor_guide_to_word(
                existing_workbook["trade_name"], existing_workbook["level_name"],
                existing_workbook["student_name"], existing_items,
            )
            existing_col_student, existing_col_instructor = st.columns(2)
            with existing_col_student:
                st.download_button("Download Previous Student Workbook", existing_student_doc,
                                   f"{trade_name}_Previous_Student_Workbook.docx",
                                   key="download_previous_student_workbook")
            with existing_col_instructor:
                st.download_button("Download Previous Instructor Guide", existing_instructor_doc,
                                   f"{trade_name}_Previous_Instructor_Guide.docx",
                                   key="download_previous_instructor_guide")
    if previous_workbooks:
        workbook_options = {
            workbook["id"]: (
                f"{workbook['student_name']} | {workbook['trade_name']} | "
                f"{workbook['level_name']} | {workbook['created_at'][:10]}"
            )
            for workbook in previous_workbooks
        }
        selected_workbook_id = st.selectbox(
            "Open a previously generated workbook",
            options=[None, *workbook_options.keys()],
            format_func=lambda workbook_id: "Select a workbook" if workbook_id is None else workbook_options[workbook_id],
            key="selected_workbook_id",
        )
        if selected_workbook_id and st.button("Load Previous Workbook"):
            workbook = db.fetch_workbook(selected_workbook_id, user_id, admin=is_superadmin)
            if workbook and workbook.get("assessment_items"):
                st.session_state.workbook_items = workbook["assessment_items"]
                st.session_state.workbook_id = workbook["id"]
                st.session_state.workbook_student_name = workbook["student_name"]
                st.session_state.workbook_trade_name = workbook["trade_name"]
                st.session_state.workbook_level_name = workbook["level_name"]
                st.success("Previous workbook loaded. No AI request or credit was used.")
                st.rerun()
        if selected_workbook_id and st.button("Delete Previous Workbook"):
            success, error = db.delete_workbook(selected_workbook_id, user_id)
            if success:
                st.session_state.pop("workbook_items", None)
                st.session_state.pop("workbook_id", None)
                st.success("Workbook deleted.")
                st.rerun()
            st.error(f"Could not delete workbook: {error}")
    else:
        st.caption("No previous workbooks found.")

    if blocked:
        if policy.get("platform_quota") == 0:
            st.warning("Your plan requires your own AI key to generate a workbook.")
        else:
            st.warning("You have no AI generation allowance available.")

    items = st.session_state.get("workbook_items")
    if items:
        st.markdown("---")
        st.success(f"Validated {len(items)} assessment items. Both documents use the same questions.")
        student_doc = export_student_workbook_to_word(
            st.session_state.workbook_trade_name,
            st.session_state.workbook_level_name,
            st.session_state.workbook_student_name,
            items,
        )
        instructor_doc = export_instructor_guide_to_word(
            st.session_state.workbook_trade_name,
            st.session_state.workbook_level_name,
            st.session_state.workbook_student_name,
            items,
        )
        st.caption("These documents are regenerated locally from the saved workbook; no AI request is made.")
        col_student, col_instructor = st.columns(2)
        with col_student:
            st.download_button(
                "📥 Student Workbook (.docx)",
                student_doc,
                f"{trade_name}_Student_Workbook.docx",
                type="primary",
            )
        with col_instructor:
            st.download_button(
                "📥 Instructor Guide (.docx)",
                instructor_doc,
                f"{trade_name}_Instructor_Guide.docx",
            )


if __name__ == "__main__":
    main()
