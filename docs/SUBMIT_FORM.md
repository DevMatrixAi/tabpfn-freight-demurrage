# Late Fee Control — submission form paste

Source: Pitch clean12 form text (SUBMIT_CLEAN_FORM_AND_README.md).
Numbers = clean12 OOF (leaky=false). No secrets.

Track: Build an agent (secondary: MCP / extension)

Project name: Late Fee Control

Description:
A shipper-side desk that flags which shipping containers are headed for port late fees (demurrage) before the invoice arrives, and says what to do about each one: push for early pickup, move it to another terminal, speed up the inland move, or book it on the next ship.

TabPFN-3.5 scores every container from the raw ops table: free-text terminal notes, vessel IDs, blank cells. The desk turns each score into a likely cost (chance × fee) and flags a container only when that's bigger than the cost of acting.

On a 1,200-container synthetic benchmark, with every container scored by a model that never saw it and columns that leak the answer removed, TabPFN-3.5 Plus ranks risk at AUC 0.911 against 0.873 for HistGBM, scikit-learn's standard gradient-boosting model. At an assumed $300 per action, acting on Plus's 195 picks saves $595,310, which is $159,723 (37%) more than acting on HistGBM's picks. Acting on all 1,200 containers would save $611,792, so Plus gets 97% of that with a sixth of the actions. When actions cost more, flagging only what matters pulls further ahead: at $500 per action Plus saves $461,792, HistGBM $407,964, and acting on everything $371,792.

With only thirty past shipments to learn from, TabPFN already ranks risk while default HistGBM can't fit yet.

Honest caveats: the containers are synthetic, generated from demurrage rules, which fits a model that itself learned from synthetic tables; real shipments will differ. The dollar math uses each container's projected fee as the amount at stake; the models never see that column, but it decides what's worth acting on and what a save is worth.

The repo ships the table and a recorded replay of real TabPFN-3.5 predictions, so judges can run the full desk without a token; one command switches to live calls.

Repo: https://github.com/DevMatrixAi/tabpfn-freight-demurrage   (after the public flip)
Video: VIDEO_LINK_TBD
