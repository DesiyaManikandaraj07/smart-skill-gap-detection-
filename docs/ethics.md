# Ethics, bias, privacy & limitations

## Privacy

- **Guest mode:** resume bytes are processed in memory; PDF is not saved as a file.
- **Signed-in mode:** derived analysis JSON is stored (skills, scores, summary) for history/admin — disclose this to users.
- Do not upload government IDs or secrets.
- Change default admin credentials before sharing a deployment.

## Hard gates vs skills

Objective filters (CGPA, years, location, degree, work auth) mirror real ATS behavior. They can make a candidate **effectively ineligible** even with excellent skills. The product surfaces this explicitly so students understand *why* a strong portfolio may still fail an automated screen.

## Bias

Skills-first scoring reduces some prestige/name leakage but does **not** eliminate bias. CGPA and location gates themselves can encode socioeconomic and geographic inequity. Treat outputs as educational signals, not hiring decisions.

## Predictions are probabilistic

Selection % is an estimate from proxy-trained models. It is **not** a guarantee of interview, offer, or rejection.

## Academic use

Built for demos and coursework with free/open-source tooling. Production hiring systems require legal review, human oversight, and audited data beyond this repository.
