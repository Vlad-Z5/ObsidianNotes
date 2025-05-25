Fully managed message queuing service, which is used to decouple microservices, distributed systems, or serverless apps

- **Queue Types:**
	- **Standard:**
		High throughput, at-least-once delivery, possible out-of-order messages
	- **FIFO:**
		First-in-first-out order, exactly-once processing (limited throughput)

- **Key Features:**
	- **Message retention:** 1 minute to 14 days
	- **Message size:** Up to 256 KB (larger via S3 + pointer)
	- **Delivery delay:** Up to 15 minutes
	- **Visibility timeout:** Prevents multiple consumers from processing the same message simultaneously
	- **Long polling** is preferred, waits for message when there is none in the queue (1 to 20 sec, best to have longest)
	- Can have duplicates or out of order if not FIFO
	- **Dead Letter Queues (DLQ):** Capture failed messages for debugging and retries