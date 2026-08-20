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
