The queue died on Friday night. Nobody noticed until Monday.

I spent the morning convinced the deploy had broken the workers, and it hadn't. The box ran out of disk because a debug flag from March was still on, writing a gigabyte of trace logs a day. Don't ask why nobody saw the alert; the alert went to a list nobody reads.

Fix took ten minutes. Cleanup took the day: prune the logs, flip the flag, move the alert to the on-call channel, write the note I should've written in March.

Lesson learned the boring way. Check the disk first.
