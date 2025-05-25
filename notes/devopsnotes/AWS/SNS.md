Pub/sub messaging service is used to decouple applications and enable fan-out messaging to multiple subscribers

- **Protocols Supported:**
	- HTTP / HTTPS
	- Email / Email-JSON
	- SMS
	- SQS
	- Lambda
	- Application (mobile push: APNs, GCM/FCM, ADM)

- **Key Features:**
	- **Topic-based:** Create topics for pub/sub workflows
	- **Message filtering:** Deliver only relevant messages to subscribers
	- **Durability:** Stores messages redundantly across multiple AZs
	- **Fan-out:** One message can trigger multiple downstream services
	- **Delivery retries:** Built-in retry logic for all endpoints
	- Can be **FIFO**
	- **DLQ, message archival, and replay**

