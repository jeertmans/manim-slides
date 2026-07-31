
# Firebase Realtime Database Sync for Manim Slides

## Usage

Simply use the `firebase_sync.html` template when rendering your slides:

```bash
manim-slides convert MainScene --one-file --use-template firebase_sync.html
```

After that, I recommend serving the generated HTML file using a simple
GitHub Pages, Vercel, or any static hosting service.
When you open the URL, you can specify the role as a presenter or guest:

- Presenter: `https://your-hosting-url.com/your-slides.html?role=presenter` (or `#presenter`)
- Guest: The presenter will have a button to copy the guest URL
(e.g., `https://your-hosting-url.com/your-slides.html?room=room-1234abcd`),
which can be shared with others.

The current template is configured to use a public Firebase
project for testing purposes.
For production use, you should create your own Firebase project
and update the configuration variables in the template accordingly.

## Example Demo

If you want to see a live demo of the Firebase sync in action,
you can check out this example presentation hosted on GitHub Pages:

- <https://liuktc.github.io/ProjectsPresentation/#presenter>

## Create your own Firebase Project

This guide explains how to set up your own Firebase Realtime Database
for syncing slides between a presenter and guests using the
`firebase_sync.html` template.

## Testing & Setup Steps

1. **Create a Firebase Project:**
   - Go to the [Firebase Console](https://console.firebase.google.com/) and
   create a new project.

2. **Enable Realtime Database:**
   - In the Firebase console, navigate to "Realtime Database"
   and click "Create Database".
   - Choose a location for your database.
   - Start in "test mode" or configure your security rules (see below).

3. **Enable Anonymous Authentication:**
   - Go to "Authentication" > "Sign-in method".
   - Enable the "Anonymous" provider.
   (This allows presenters to securely claim their rooms
   without requiring guests to login).

4. **Get Firebase Config:**
   - Go to your Project settings.
   - Under "Your apps", add a Web app to get your Firebase configuration.
   You will need:
     - `apiKey`
     - `authDomain`
     - `databaseURL`
     - `projectId`

5. **Fill Template Variables:**
   - Provide the Firebase configuration variables when rendering `firebase_sync.html`:
     - `firebase_api_key`
     - `firebase_auth_domain`
     - `firebase_database_url`
     - `firebase_project_id`

6. **Serve and Test:**
   - Serve the rendered HTML.
   - **Presenter:** Open the URL with `?role=presenter` (or `#presenter`).
   The URL will automatically be updated to include a uniquely generated
   room ID (e.g., `?room=room-1234abcd`).
   A button will automatically appear for the presenter to copy the guest URL.
   - **Guest:** Just open the guest URL (e.g., `?room=room-1234abcd`)
   in another tab or share it with others.
   Guests will see the current slide and will update in real-time as
   the presenter changes slides.

## Security Rules (Recommended)

To ensure that only the presenter who created the room can change the
slide state, and anyone can read from a room, you should
enforce a security rule.

In the Firebase Console under **Realtime Database > Rules**, configure the following rules:

```json
{
  "rules": {
    "rooms": {
      "$roomId": {
        // Anyone can read room state
        ".read": true,

        // Writes are allowed if:
        // 1. User is authenticated (Anonymous Auth)
        // 2. The write operation preserves their UID as presenterId,
        // or the existing room is already owned by this UID.
        ".write": "auth != null && (
          (!data.exists() &&
            newData.child('meta/presenterId').val() === auth.uid) ||
          (data.child('meta/presenterId').val() === auth.uid &&
            newData.child('meta/presenterId').val() === auth.uid)
        )"
      }
    }
  }
}
```

This prevents malicious guests from changing the slide by restricting
write access to the anonymously authenticated presenter.
