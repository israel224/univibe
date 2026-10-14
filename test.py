UniVas — Fix and Expand Search

Update the existing search feature to work like TikTok or Facebook search.

1. Search for anything

* Users can search for news, Nigeria, current events, topics, keywords, hashtags, and anything else people have posted about.
* Show posts whose text or captions match the search, including text posts, photos, and videos.
* For example, if someone searches “Nigeria news,” show relevant posts other users have published about Nigeria and the news.
* Users can also search for usernames and find people.
* Show relevant matching results from the existing UniVas database. Do not invent posts or news that nobody has published.

2. Search must work independently

* Tapping the search bar must open the search interface, NOT take users to Friends.
* Users must be able to type a query and see matching results directly.
* If no posts or users match, display a clear message such as “No results found” or “No posts found yet.”
* An empty result must NEVER redirect users to Friends, Feed, or another screen.
* Friends must remain a separate feature.

3. New-app behaviour

* UniVas is new, so there may initially be no posts about a particular topic. Show an honest empty-results message until matching posts exist.
* As people publish relevant posts, searches should find them without requiring a code change for every new topic.

4. Preserve existing features

* Keep the current Saved Posts work and existing profile improvements.
* Preserve login, permissions, blocking, and privacy protections.
* Do not remove or replace existing functionality unnecessarily.
* Use the current Flet 1.0.2 setup and existing Supabase database.
* Inspect the current code and database structure before making changes. Do not invent database columns or run destructive SQL.
* Back up the current working test.py before editing.
* Do not deploy the app or modify Android project files.

5. Testing
Verify that:

* Searching for an existing username finds that person.
* Searching for a word or topic finds matching published posts.
* Matching text posts, photo posts, and video posts can appear.
* Searching for a topic with no matching posts shows an empty-results message.
* Tapping Search never redirects to Friends.
* Existing login, profiles, Saved Posts, and privacy protections remain intact.

Return the complete updated test.py, a backup, and any necessary SQL in a separate, clearly labelled script. Explain which SQL is read-only and which SQL changes the database. Do not claim real-device or live-database tests unless they were actually performed.
