## How ward analytics becomes a business

Hospitals pay for a small demonstration to see whether an assistant can answer the questions that come up every shift. A fixed fee covers the sample data, the working demo, and an accuracy review. Most of that fee pays for the specialists who design the tests and check the answers.

If the demonstration succeeds, the next source of revenue is an implementation contract to connect hospital systems and roll the tool out across wards. Ongoing subscriptions cover software and support, typically priced by bed or facility. Implementation and subscriptions are the larger opportunity. This demo focuses on the first sale and whether staff can trust the answers it produces.

## Where time and capacity disappear

- **Handover takes detective work.** A count of everyone admitted can look reasonable even when it mixes patients in labor with patients who have gone home. The next shift has to check each record to tell who still needs a bed or follow-up.
- **An empty bed may still be unusable.** A bed being cleaned or repaired can look empty on an occupancy report. The difference only becomes obvious when someone tries to place a patient and has to find another bed.
- **Changes can hide between readings.** A list of the latest blood pressures can miss a steady rise across several checks. The team has to line up the readings in time to see it, and an alert marked as seen can still matter at handover.
- **The schedule leaves gaps between records.** A planned cesarean can have a time, room, and named provider even when the roster lacks anesthesia coverage for that date. An expected discharge can also look firm until staff check the prediction and the small number of stays they can compare against.

## What the ward snapshot records

Admissions tell you who is on the ward. Bed and room records tell you where they are and which spaces are usable. Staff rosters, procedure orders, labor exams, readings, and alerts supply the context for each answer. These records belong together because each one describes a different part of the same decision.

The demo follows one synthetic ward at **8:00 a.m. on February 13, 2026**. The roster covers three calendar days. The other records include events leading up to the snapshot and upcoming procedure orders. Questions about today and tomorrow use that fixed clock.

## How MaterniFlow answers

MaterniFlow checks which tables and fields are available, writes a read-only query, and explains the result in plain English. Ask for the SQL to see how it counted. For an admission sequence it can draw a diagram, and for a series of timed readings it can show a chart.

## What to ask and how to read the answers

- **Shift handover.** How many patients are on the ward? Where are they in their stay? Whose latest labor exam shows the greatest dilation? A patient waiting for discharge still counts as active.
- **Bed capacity.** Which rooms have a bed ready now? How does occupancy compare across room types? Cleaning is a separate state, and occupancy uses all beds of that type as its denominator.
- **Risk monitoring.** Which alerts are pending? How has blood pressure moved across recorded checks? Read the observation time alongside the value and use the stored risk rating as part of this simulation.
- **Care scheduling.** What procedures are coming up? Who is on the roster? How long are patients expected to stay after delivery? Measure postpartum hours from delivery. Only one stay has a recorded discharge, so use that comparison as an example rather than a ward-wide accuracy estimate.

## From a demo to a working system

MaterniFlow is deliberately read-only so people can explore the simulated ward and verify its answers. The same architecture can add tools that update an order or bed assignment. A real rollout would need staff permissions and an audit trail that records who changed what and when.
