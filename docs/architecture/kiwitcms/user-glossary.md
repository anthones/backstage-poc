# KiwiTCMS: User glossary

[Adoption overview](README.md) · [Backstage user glossary](../backstage/user-glossary.md)

You are a QA engineer preparing to test a service and report the results.
Company access, menus, and workflows can differ from the official guides.

## 1. Sign in and find your work

Open the company-provided KiwiTCMS address and use the access method your team provides.
Ask your team lead for help if you cannot sign in.

| Term      | Meaning                                                                       |
| --------- | ----------------------------------------------------------------------------- |
| Dashboard | Your starting view of assigned test runs and related test plans.              |
| Product   | The software you will test. Check that you have selected the correct product. |

Open an assigned run from the dashboard, or use search.
Check its purpose before you edit it.

[Official guide: Home page and dashboard](https://kiwitcms.readthedocs.io/en/latest/guide/introduction.html#getting-to-know-the-tcms-home-page)

## 2. Check the test scope

| Term            | Meaning                                                                   |
| --------------- | ------------------------------------------------------------------------- |
| Test plan       | The testing purpose, approach, and collection of test cases and runs.     |
| Product version | The product release or development version associated with your testing.  |
| Reference link  | A link to supporting information, such as a requirement or specification. |

Find your plan. Read its scope and linked requirements.
Confirm which features and risks you must test. Ask the plan owner about gaps before you start.

[Official guide: Test plans](https://kiwitcms.readthedocs.io/en/latest/guide/testplan.html)

## 3. Review the test cases

| Term                     | Meaning                                                                  |
| ------------------------ | ------------------------------------------------------------------------ |
| Test case                | A reusable description of a test scenario.                               |
| Prerequisites            | The setup, test data, and conditions needed before you follow the steps. |
| Action                   | A step you perform during the test.                                      |
| Expected result / Effect | What should happen after an action.                                      |

Read the case. Resolve unclear instructions before execution.
Check that the case still matches the requirement.
A case describes the test; a product version or build identifies the software under test.

[Official guide: Writing a test case](https://kiwitcms.readthedocs.io/en/latest/guide/appendix.html)

## 4. Prepare the run

| Term           | Meaning                                                                 |
| -------------- | ----------------------------------------------------------------------- |
| Test run       | A set of selected cases and their execution results for a testing task. |
| Build          | The specific software build you will test.                              |
| Environment    | Where you test, including relevant system settings and dependencies.    |
| Confirmed case | A case ready for execution. Only confirmed cases can be added to a run. |

Select the correct build and cases. Identify the environment in the agreed run notes or tags.
Use a separate run for each environment and build combination.
Check the assigned tester.

[Official guide: Create a test run](https://kiwitcms.readthedocs.io/en/latest/guide/testrun.html#creating-a-test-run)

## 5. Execute and record the outcome

| Term             | Meaning                                                                                       |
| ---------------- | --------------------------------------------------------------------------------------------- |
| Test execution   | The record that connects a case with its result, comments, and defects in a run.              |
| Actual result    | What you observed when you followed the steps.                                                |
| Execution status | The outcome or progress state of that execution. It differs from the case's readiness status. |
| Evidence         | Information that supports the result, such as logs, screenshots, or a recording.              |

Expand the execution row. Follow the case and compare actual and expected results.
Add a comment with the outcome and evidence links. Select the appropriate configured status.
Use your team's status definitions for failures, blocked work, and incomplete tests.
For a defect, record the Jira key and URL in the comment. Use an issue tracker link if configured.

[Official guide: Execute a test run](https://kiwitcms.readthedocs.io/en/latest/guide/testrun.html#executing-a-test-run)

## 6. Retest and keep the history

| Term   | Meaning                                                                   |
| ------ | ------------------------------------------------------------------------- |
| Retest | Another check after a fix or a change in conditions.                      |
| Clone  | A copy used to prepare a new run. Check its build and details before use. |

Create or clone a run for a new build. Keep earlier results and evidence.
For a retest, use your team's process to keep both outcomes traceable.
Open a case's **Executions** view to compare results across runs.

[Official guide: Testing workflow and execution history](https://kiwitcms.readthedocs.io/en/latest/guide/introduction.html#testing-workflow-example)

## 7. Share progress and remaining gaps

| Term       | Meaning                                                                                                           |
| ---------- | ----------------------------------------------------------------------------------------------------------------- |
| Run status | Whether the run is undefined, running, or finished. This differs from each execution's result.                    |
| Coverage   | The requirements or risks checked by your cases and results. Passed-case counts alone do not prove full coverage. |

Share the run link, build, environment, outstanding tests, and defect links.
State what remains untested. A finished run or a passing result does not approve a release.
Mark the run **Finished** only after the agreed review: its run status cannot then change.

[Official guide: Change a test run's status](https://kiwitcms.readthedocs.io/en/latest/guide/testrun.html#changing-the-status-of-a-test-run)
