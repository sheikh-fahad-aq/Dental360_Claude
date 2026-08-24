# Architecture change log

Appended automatically by `.claude/hooks/record_change.py` on every file edit. Do not
hand-edit and do not delete. One line per file per day, tagged with the skill that
documents it, so that keeping this record costs no model tokens.

Only changes to the two applications are recorded. Edits under `.claude/` are excluded --
this tree's own git history already covers them, and without that exclusion a session spent
writing skills would fill the log with itself.

Being listed here does **not** mean a skill is wrong. `/skill-sync` reads this alongside
`.stale.json` to work out what actually needs updating.

## 2026-08-18

Recording starts here, with the initial `.claude` tooling in place: `CLAUDE.md`, 22 feature
skills, 5 agents, 8 commands, 3 hooks and the ownership map. No application code was changed
in that work, which is why nothing is listed under this date yet.
- `PMS_React/src/api/ledger.js` — fe-ledger (Edit) [final]
- `PMS_React/src/components/patient-detail/charting/useMultiCodeExpansion.js` — fe-charting (Write) [01c29a5c]
- `PMS_React/.claude/launch.json` — fe-platform (Write) [01c29a5c]
- `PMS_React/src/components/patient-detail/charting/useMultiCodeExpansion.js` — fe-charting (Write) [4db310df]

## 2026-08-19
- `PMS_React/src/components/patient-detail/charting/useChartingMultiCodes.js` — fe-charting (Write) [4db310df]
- `PMS_React/src/components/patient-detail/charting/chartingMultiCodes.js` — fe-charting (Write) [4db310df]
- `360_Flask_Appointment/app/treatment_plans_v2_routes.py` — be-platform (Write) [8cae5336]
- `360_Flask_Appointment/tests/test_treatment_plans.py` — be-charting (Write) [8cae5336]
- `PMS_React/src/api/treatmentPlans.js` — fe-platform (Write) [8cae5336]
- `PMS_React/src/hooks/usePatientTreatmentPlans.js` — fe-patient-chart (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/tx-plans/txPlanFormat.js` — fe-patient-chart (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/tx-plans/TxPlansSection.jsx` — fe-patient-chart (Write) [8cae5336]
- `360_Flask_Appointment/tests/test_repro_defer.py` — be-charting (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/tx-plans/txPlanUi.jsx` — fe-patient-chart (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/treatmentListingFilters.js` — fe-charting (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/RecommendedTreatmentTable.jsx` — fe-charting (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/AddToTreatmentPlanModal.jsx` — fe-charting (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/ClinicalHistoryTable.jsx` — fe-charting (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/tx-plans/builder/TreatmentPlanPatientPreview.jsx` — fe-patient-chart (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/ChartEntryDetailPanel.jsx` — fe-charting (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/ChartEntryDetailPanel.jsx` — fe-charting (Edit) [8cae5336]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/TreatmentBulkActionBar.jsx` — fe-charting (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/TreatmentListingPanel.jsx` — fe-charting (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/TreatmentPlansTable.jsx` — fe-charting (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/AddToTreatmentPlanModal.jsx` — fe-charting (Edit) [8cae5336]
- `PMS_React/src/pages/SharedTreatmentPlanPage.jsx` — fe-platform (Write) [8cae5336]
- `PMS_React/src/config/routes.js` — fe-platform (Edit) [8cae5336]
- `PMS_React/src/components/patient-detail/tx-plans/builder/TreatmentPlanDocument.jsx` — fe-patient-chart (Write) [8cae5336]
- `PMS_React/src/components/AppRoutes.jsx` — fe-platform (Edit) [8cae5336]
- `PMS_React/src/components/patient-detail/tx-plans/builder/RecommendedTreatmentRail.jsx` — fe-patient-chart (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/tx-plans/builder/TreatmentPlanActivity.jsx` — fe-patient-chart (Write) [8cae5336]
- `PMS_React/src/components/patient-detail/tx-plans/builder/TreatmentPlanBuilder.jsx` — fe-patient-chart (Write) [8cae5336]
- `PMS_React/src/pages/SharedTreatmentPlanPage.jsx` — fe-platform (Edit) [8cae5336]
- `PMS_React/.claude/launch.json` — fe-platform (Write) [8cae5336]

## 2026-08-20
- `PMS_React/src/components/patient-detail/charting/treatment-listing/treatmentListingCsv.js` — fe-charting (Write) [48a5597b]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/TreatmentListingMenu.jsx` — fe-charting (Write) [48a5597b]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/ProcedureDetailsModal.jsx` — fe-charting (Write) [48a5597b]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/procedureJourney.js` — fe-charting (Write) [48a5597b]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/treatmentListingCsv.js` — fe-charting (Edit) [48a5597b]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/ProcedureDetailsModal.jsx` — fe-charting (Edit) [48a5597b]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/TreatmentListingMenu.jsx` — fe-charting (Edit) [48a5597b]
- `PMS_React/src/components/patient-detail/charting/treatment-listing/TreatmentListingPanel.jsx` — fe-charting (Edit) [48a5597b]
- `PMS_React/src/api/charting.js` — fe-charting (Edit) [48a5597b]
- `PMS_React/src/components/patient-detail/tx-plans/builder/treatmentPlanDraft.js` — fe-patient-chart (Write) [48a5597b]
- `PMS_React/src/components/patient-detail/tx-plans/builder/ProcedureLocationPopover.jsx` — fe-patient-chart (Write) [48a5597b]
- `PMS_React/src/components/patient-detail/tx-plans/builder/RecordManualResponseModal.jsx` — fe-patient-chart (Write) [8514f8d7]
- `PMS_React/src/components/patient-detail/tx-plans/builder/RecordManualResponseModal.jsx` — fe-patient-chart (Edit) [8514f8d7]
- `PMS_React/src/components/patient-detail/tx-plans/builder/TreatmentPlanActionsMenu.jsx` — fe-patient-chart (Write) [8514f8d7]
- `PMS_React/src/components/patient-detail/tx-plans/builder/TreatmentPlanPresentation.jsx` — fe-patient-chart (Write) [8514f8d7]
- `PMS_React/src/components/patient-detail/tx-plans/builder/SendTreatmentPlanModal.jsx` — fe-patient-chart (Write) [8514f8d7]
- `PMS_React/src/components/patient-detail/tx-plans/builder/SendTreatmentPlanModal.jsx` — fe-patient-chart (Edit) [8514f8d7]
- `360_Flask_Appointment/app/treatment_plans_v2_routes.py` — be-treatment-plans (Edit) [8514f8d7]
- `PMS_React/src/components/patient-detail/tx-plans/builder/TreatmentPlanPresentation.jsx` — fe-patient-chart (Edit) [8514f8d7]
- `PMS_React/src/components/patient-detail/tx-plans/builder/TreatmentPlanVersionMenu.jsx` — fe-patient-chart (Write) [8514f8d7]

## 2026-08-21
- `PMS_React/src/hooks/usePatientChartFindings.js` — fe-patient-chart (Write) [f9b40d8f]
- `PMS_React/src/components/patient-detail/tx-plans/ChartFindingsCard.jsx` — fe-patient-chart (Write) [f9b40d8f]
- `PMS_React/src/components/patient-detail/tx-plans/TxPlansTable.jsx` — fe-patient-chart (Write) [f9b40d8f]
- `PMS_React/src/components/patient-detail/tx-plans/TxPlansSection.jsx` — fe-patient-chart (Write) [f9b40d8f]

## 2026-08-24
- `PMS_React/src/components/patient-detail/tx-plans/builder/treatmentPlanPdf.js` — fe-patient-chart (Write) [f9b40d8f]
- `PMS_React/src/components/patient-detail/tx-plans/builder/ComparePlansModal.jsx` — fe-patient-chart (Write) [f9b40d8f]
- `PMS_React/src/components/patient-detail/tx-plans/builder/comparePlans.js` — fe-patient-chart (Write) [f9b40d8f]
- `PMS_React/src/pages/SharedTreatmentPlanPage.jsx` — fe-platform (Write) [5e6757a3]
- `PMS_React/src/components/patient-detail/tx-plans/builder/emailTemplate.js` — fe-patient-chart (Write) [5e6757a3]
- `PMS_React/src/components/patient-detail/tx-plans/builder/EmailTemplateEditor.jsx` — fe-patient-chart (Write) [5e6757a3]
