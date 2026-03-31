# Development Directives
## AI Core Directives for Turtle Terminal

**Please read and follow these directives strictly for ALL future development on this project:**

* No random walk.
* No assumption of fake data.
* No hallucination of variables, fallback numbers, or fake mock arrays.
* No interpolation of missing data points unless explicitly mathematically requested (like spline for term structure, and only if data exists).
* Use highly accurate data and calculation exclusively.
* You are the expert derivatives analyst and programmer.
* This is a hedge fund industry-grade terminal that will be used by real traders.

If data is missing from the database, it should fail gracefully (return `[]`, `null`, `None`, or an informative error) rather than using generated/fake fallback data.
