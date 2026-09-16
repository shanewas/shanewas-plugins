Our deploy script failed every third Friday, yet nobody kept notes long enough to prove the pattern.
It wasn't random.
The failures always landed near midnight, which meant whoever carried the pager spent Saturday digging through logs.
Morale sank fast.
We blamed the cloud vendor first, because blaming the vendor buys a quiet week while you hunt the real cause.
The vendor shrugged.

I pulled three months of deploy logs onto my laptop in order to read them on the train without waking the baby.
Patterns hide in boredom.
Around two in the morning, the script always paused between uploading the bundle plus restarting the workers.
That pause killed us.
A lock file survived from the previous run, so the new workers waited on a gate that never opened.
Classic leftover state.

The script wrote its lock into a temp folder that the night janitor wiped, except on Fridays when backups held the disk busy.
Fridays explained themselves.
Nobody had documented the temp folder, since the author took that context along when he left.
We've all done that.
Generally speaking, scripts outlive their authors, then the team inherits puzzles disguised as automation.
This one stank.

We deleted the lock file dance entirely, replacing it with a queue that the workers drain at their own pace.
Locks lie anyway.
I also added a heartbeat the deploy checks before it calls anything done, so partial uploads can't masquerade as success.
Small change, big relief.
The next Friday passed quietly, although I stayed awake refreshing the dashboard like a nervous parent.
Nothing broke.

Retries came next, because the bundle upload sometimes stalled halfway, leaving a corrupt half behind.
Half files poison everything.
Now the script checksums the bundle before it restarts anything, then it keeps the old workers until the new ones answer.
Blue-green on a budget.
We kept the old path behind a flag for a month in order to retreat fast if the new flow misbehaved.
Paranoia pays rent.

The flag expired without drama, which felt strange after years of dreading every second Friday.
Calm tastes weird.
Deploys ultimately became boring, the highest praise any release pipeline can earn from tired engineers.
Boring ships product.
Our pager stayed silent through quarter end, while other teams fought fires we couldn't even see.
We gloated quietly.

I wrote the whole saga into the runbook, including the wrong turns, because future-me forgets everything within weeks.
Runbooks beat memory.
My drawings look like a toddler attacked the page with crayons, yet they explain the lock bug better than prose ever did.
Draw more diagrams.

We also fixed the alert routing, moving night pages to the person who shipped last instead of a dead mailing list.
Ownership sharpens attention.
Nobody wants a midnight call about their own merge, so folks started testing Friday deploys before lunch.
Incentives work fast.
One engineer built a tiny dashboard that shows deploy health at a glance, sparing everyone the log spelunking we endured.
Adoption took days.

The dashboard ultimately replaced three separate status pages, none of which agreed with each other anyway.
One screen wins.
People trust a single green dot more than paragraphs of status text, even when the dot hides messy details.
Dots don't argue.
We kept the messy details one click away for skeptics, since trust without evidence rots into superstition.
Skeptics keep systems honest.

A year later, Friday deploys feel ordinary, like brushing teeth or locking the office door.
Ordinary feels great.
New hires never learn the old fear, which means the story only survives in the runbook plus my drawings.
Good riddance, mostly.
I still flinch when my phone buzzes after midnight, then I remember the green dot plus roll over.
Sleep beats heroics.
If your own Fridays smell haunted, start with the temp folders, for ancient scripts bury their secrets there.
You'll thank yourself.

We added a staging deploy that mirrors Friday load, so surprises surface on Tuesday when everyone's awake.
Tuesdays forgive mistakes.
Staging caught three separate bugs in its first month, bugs that would've bitten us during quarter end.
Staging earns trust.
I don't trust a pipeline I haven't watched fail, so we break staging on purpose every quarter.
Chaos teaches calm.

New folks pair with veterans for their first Friday deploy, which spreads the lore faster than any document.
Lore beats manuals.
We've turned the scary evening into a casual ritual with snacks, and the new folks love it.
Snacks fix culture.
It's funny how a lock file taught us more than any postmortem template ever has.
Files outlive intentions.
That's the whole story, minus the swear words we screamed at dashboards that lied to our faces.
Don't trust dashboards.

If you inherit a haunted script, read it end to end before you change a single line.
Reading beats guessing.
You'll spot the weird timestamp check or the sleep call that nobody can explain.
Ask about it.
Someone always knows why the weird line exists, and that someone usually loves telling the tale.
Listen first.
