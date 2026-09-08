# Explore your first case

Start with [the fictional Meridian atlas](https://stunspot.github.io/red-threads/demo.html). You can explore that generated result without installing a skill, running Python, or supplying private records. Every name, document, amount, and quotation in this example is invented teaching material.

The question is concrete: **who can influence a proposed compute-licensing rule, by which mechanism, and what would distinguish broad funder direction from narrower control or independent agreement?**

## Generate your own atlas

If you want a local copy, first [obtain the complete skill from GitHub](installation.md). In a local clone, open a terminal in `src/red-threads`, the folder containing `SKILL.md`. If you use a published skill ZIP when available, open the extracted `red-threads` folder instead. These commands use the bundled example and create a new HTML file in the parent directory, outside the skill folder. If that parent is not writable, choose a new absolute output path in your own workspace.

1. Check the case.

   ```text
   python scripts/red_threads.py validate examples/meridian-case.json
   ```

   Expect JSON containing `"valid": true`. Validation checks the record structure and references; the teaching facts remain fictional.

2. Generate the atlas.

   ```text
   python scripts/red_threads.py render examples/meridian-case.json --output ../meridian-atlas.html
   ```

   Expect `"ok": true` and the output path. If that filename exists, use a new destination such as `../meridian-atlas-2.html`. The tool refuses to overwrite it.

3. Open the generated HTML file in a modern browser through your system's usual file-opening route. If your host blocks local browser access, open it yourself where permitted or use the public fictional demo. Keep private case data out of the public demo.

You should see **The Meridian File - fictional training case**, the investigation question, and views named **Atlas**, **Timeline**, **Explanations**, **Leads**, **Actor games**, and **Sources**. A successful render confirms generation; inspect the browser result to confirm usable display on your own device.

## Make three connections earn their meaning

First, find **Cobalt** in **Find** and select **Go**, or select the relevant entity from the map. Inspect its grant and approval relationships. The $1.8 million award and the $900,000 installment describe the same grant at different stages. Adding them would manufacture spending. The approval right applies to the funded brief. That is a real mechanism inside the fiction; it does not give Cobalt general command over everyone nearby.

Next, open **Sources** and choose **FICTIONAL: Streamcast retelling** using **Select source to inspect**. Follow its ancestry through Ledger and Sentinel to the award announcement. Those retellings preserve a single recorded origin for the broad direction allegation. Extra publishers have not created extra witnesses.

Finally, open **Explanations**. Compare **Broad patron direction**, **Bounded grant control plus parallel incentives**, and **Shared briefing channel without a central controller**. Inspect the support, challenges, assumptions, and next tests. The documented July revision packet cannot explain Astera's earlier June endorsement. A useful investigation notices that timing problem and changes the next question.

You have reached the first result when you can explain one supported mechanism, identify one inference the sources do not establish, and name a record that could distinguish the remaining explanations.

## Explore without changing the evidence

In **Layers, dates & structural tools**, set **Effective on date** to examine a period. **Keep unknown intervals** retains relationships whose dates are incomplete. An open end means no termination is recorded; it does not verify current employment.

Use **Trace from**, **Trace to**, and **Trace directed path** to inspect a route. Read each arrow's actual verb. Removing a node under **Structural scenario** changes visible connectivity only. To return, choose **No removal · observed graph**. **Clear trace**, **Reset filters**, and **Overview** restore their corresponding presentation choices.

Select **Save view** to download a view snapshot. **Load view** restores a compatible snapshot for the same case. This saves attention and filters, not new evidence. Keep the case JSON as well.

## Ask the AI to continue

After [skill discovery](installation.md), try:

```text
Use RED THREADS on the fictional Meridian case. Explain the
strongest supported mechanism and the strongest useful rival.
Choose one next record that could change the assessment. Preserve
the distinction between an award, a payment, and an approval right.
```

Then move to [your own investigation](investigations.md). If a command, display, or saved view fails, [recovery](recovery.md) gives the next check.