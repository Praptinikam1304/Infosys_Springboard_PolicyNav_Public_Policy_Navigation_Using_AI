\# PolicyNav: Milestone 4 - Administration \& User Personalization



Milestone 4 marks the transition of PolicyNav from a functional AI tool into a mature, manageable platform. This update introduces a comprehensive administrative command center for monitoring platform health, alongside a personalized and highly secure user dashboard.



\## 1. Admin Command Center \& Analytics

The newly integrated Admin panel provides administrators with deep insights into platform usage, security metrics, and user management capabilities.



\* \*\*Complete User Lifecycle Management\*\*: Administrators can view the entire user base, promote standard users to Admin status, manually lock/unlock accounts exhibiting suspicious behavior, and securely delete users from the database.

\* \*\*Live Security Monitor\*\*: A dedicated security tab tracks failed login attempts and displays accounts that are currently locked out due to exceeding the maximum attempt threshold. Admins can clear all lockouts with a single click.

\* \*\*Granular User Activity Logs\*\*: Admins can select any specific user to view a chronological log of their interactions, including their exact RAG search queries, requested summaries, and the AI's generated responses.

\* \*\*Interactive Analytics Dashboard\*\*: Utilizing \*\*Plotly Express\*\* and \*\*Streamlit Autorefresh\*\*, the dashboard provides real-time, interactive data visualization, including:

&nbsp; \* \*\*Language Distribution\*\*: A pie chart showing the breakdown of native languages requested by users.

&nbsp; \* \*\*Feature Popularity\*\*: Bar charts comparing the usage of RAG Search vs. Summarization vs. Knowledge Graph.

&nbsp; \* \*\*Daily Activity Trends\*\*: Line graphs tracking platform usage over time.

&nbsp; \* \*\*Active User Leaderboard\*\*: A funnel chart highlighting the top 10 most active users.

&nbsp; \* \*\*Model Usage\*\*: A custom gauge charting the volume of HuggingFace transformer inferences.

\* \*\*Feedback Analysis \& Export\*\*: The system captures user ratings and comments across all features. Admins can view this feedback chronologically, visualize common themes using a dynamically generated \*\*WordCloud\*\* (`matplotlib` + `wordcloud`), and export the raw data as a CSV for external reporting.





\## 2. User Dashboard \& Profile Personalization

This module vastly improves the individual user experience, giving users autonomy over their data and identity while maintaining strict security protocols.



\* \*\*Identity \& Avatars\*\*: Users can now upload custom profile pictures (`.png`, `.jpg`) which seamlessly integrate into the sidebar and dashboard headers, replacing the default initial-based chips.

\* \*\*Secure Email Updates\*\*: Users can update their registered email addresses. To prevent account hijacking, this action requires verifying a 6-digit OTP sent via email before the database is updated.

\* \*\*Advanced Password Management\*\*: The password update flow now includes strict strength validation (requiring uppercase, lowercase, numbers, and 8+ characters) and checks against a password history ledger to prevent users from reusing their last 3 passwords.

\* \*\*UI/UX Polishing\*\*: The entire application now features a cohesive, custom dark theme ("Junaid's dark theme") with specialized CSS for custom button gradients, sleek form inputs, interactive hover-cards in the history tables, and cleanly segregated tabs.







\## Installation \& Execution (Milestone 4 Additions)



To support the new data visualization and image processing features, install the additional dependencies:



\### Dependency Setup

```bash

pip install wordcloud matplotlib plotly pandas -q


