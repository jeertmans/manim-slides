# Sync Presentation

Manim Slides provides a built-in template (`firebase_sync.html`) to sync your slide progression across multiple devices in real-time. This is useful when you want to share your presentation with an audience on their own devices (e.g. virtual conference) without relying on screen sharing (that can be laggy and low-quality).

This feature relies on [Firebase Realtime Database](https://firebase.google.com/products/realtime-database).

## Usage

You can use the `firebase_sync.html` template when rendering your slides into an HTML presentation:

```bash
manim-slides convert MainScene --one-file --use-template firebase_sync.html
```

Afterward, serve the generated HTML file using GitHub Pages, Vercel, or any static hosting service.

When you open the URL, you can specify your role:
- **Presenter:** Append `?role=presenter` (or `#presenter`) to the URL (e.g., `https://your-hosting-url.com/your-slides.html?role=presenter`).
- **Guest:** The presenter will have a button to copy the guest URL (e.g., `https://your-hosting-url.com/your-slides.html?room=room-1234abcd`), which can be shared with others or opened on the display computer.

The guests will see the current slide and will update in real-time as the presenter changes slides.

:::{warning}
The default template is configured to use a public Firebase project for testing purposes.
For production, you should create your own Firebase project and provide the
configuration variables (see [Create your own Firebase Project](#create-your-own-firebase-project)).
:::

## Example Demo

:::{note}
If you want to see a live demo of the Firebase sync in action, you can check out
this example presentation hosted on the project documentation:

- [Live demo (presenter view)](../_static/firebase_sync_demo.html#presenter)
:::

## Create your own Firebase Project

This guide explains how to set up your own Firebase Realtime Database for syncing slides.

### Setup Steps

1. **Create a Firebase Project:**
   Go to the [Firebase Console](https://console.firebase.google.com/) and create a new project.

2. **Enable Realtime Database:**
   In the Firebase console, navigate to **Realtime Database** and click **Create Database**. Choose a location for your database and start in "test mode" or configure your security rules (see below).

3. **Enable Anonymous Authentication:**
   Go to **Authentication** > **Sign-in method**. Enable the **Anonymous** provider. This allows presenters to securely claim their rooms without requiring guests to login.

4. **Get Firebase Config:**
   Go to your Project settings. Under **Your apps**, add a Web app to get your Firebase configuration. You will need:
   - `apiKey`
   - `authDomain`
   - `databaseURL`
   - `projectId`

5. **Fill Template Variables:**
   Provide the Firebase configuration variables when rendering `firebase_sync.html`. You can pass these as arguments via the command line with `-c` (config):

   ```bash
   manim-slides convert MainScene --use-template firebase_sync.html \
     -c firebase_api_key=YOUR_API_KEY \
     -c firebase_auth_domain=YOUR_AUTH_DOMAIN \
     -c firebase_database_url=YOUR_DATABASE_URL \
     -c firebase_project_id=YOUR_PROJECT_ID
   ```

### Security Rules (Recommended)

:::{warning}
To ensure that only the presenter who created the room can change the slide state, and anyone can read from a room, you should enforce a security rule.
:::

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

This prevents malicious guests from changing the slide by restricting write access to the anonymously authenticated presenter.
