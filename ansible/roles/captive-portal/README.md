# captive-portal role

Installs and configures the ConnectBox captive portal. The portal intercepts
HTTP requests from newly-connected Wi-Fi clients and directs them to
`http://gowifi.org`, which detects whether the device is routing through
cellular data and, if so, instructs the user to disable it before redirecting
them back to the ConnectBox content.

## How it works

The portal is a Flask application (`simple-offline-captive-portal`) served by
gunicorn. All DNS on the AP resolves to the ConnectBox IP, so every HTTP
request a connected device makes hits the portal first.

Each OS has its own captive portal detection flow — it sends a probe HTTP
request to a known URL and checks the response. The portal intercepts those
probes and returns non-standard responses, which causes the OS to display a
"Sign in to network" sheet or notification. Inside that sheet the user sees
the `gowifi.org` URL and instructions.

### gowifi.org

`gowifi.org` is an external service specifically designed for this flow. It
detects whether the incoming request arrived via cellular data or Wi-Fi:
- **Cellular**: tells the user to turn off cellular data, then retry
- **Wi-Fi**: redirects the user directly to the ConnectBox portal

This is necessary because modern smartphones often prefer cellular over a
Wi-Fi network that appears to have no internet access, meaning the captive
portal probe itself goes via cellular and the OS never shows the sign-in
sheet.

## OS support matrix

ConnectBox is deployed globally, including regions where phones are
redistributed from wealthier countries. Support must cover devices many years
old as well as current models.

| OS | Version | Link type | OK button | Notes |
|---|---|---|---|---|
| iOS | < 9 | text | No | Old redistributed devices |
| iOS | 9 | href | No | |
| iOS | 10 | text | No | Links open inside captive browser — intentionally kept as text |
| iOS | 11 | href | No | |
| iOS | 12–18+ | href | No | WKWebView (iOS 14+) supports opening links in Safari |
| Android | < 6 | text | No | Old redistributed devices |
| Android | 6+ (Dalvik UA) | text | Yes | Dalvik agent; OK press completes handshake |
| Android | 7.1+ (X11 UA) | text | Yes | X11-style UA does not contain "Android"; OK button required to POST ack flag to `/generate_204` so the OS receives its 204 and dismisses the portal |
| macOS | < 10.12 | text | No | Old devices |
| macOS | 10.12 (Sierra) | href | No | |
| macOS | 10.13 (High Sierra) | href | No | |
| macOS | 10.14–10.15, 11–15+ | href | No | Includes Big Sur through Sequoia; ua_parser may report 11+ as major≥11 or as 10.16 |
| Windows 10 | Any | text | No | NCSI probe on `/ncsi.txt` |
| Windows 11 | Any | text | No | NCSI probe on `/connecttest.txt` |
| Kindle Fire | Any | text | No | Probe on `/kindle-wifi/wifistub.html` |

### RFC 8908 (Captive Portal API)

The portal also serves `/.well-known/captive-portal` per RFC 8908. iOS 14+,
Android 11+, and macOS Monterey+ query this endpoint to discover the portal
URL directly, before falling back to probe-URL interception. Older devices
never request this URL, so it has no impact on them.

## Local modifications to upstream package

The portal is installed from the upstream
`ConnectBox/simple-offline-captive-portal` GitHub repository via pip. After
installation, Ansible overwrites `views.py` with
`files/captiveportal_views.py` from this role. This file contains all
upstream logic plus the following additions and fixes:

- **Windows 11**: added `/connecttest.txt` route
- **RFC 8908**: added `/.well-known/captive-portal` JSON endpoint
- **Android OK button**: fixed `device_requires_ok_press()` to return `True`
  for the Android 7.1+ X11-style UA (which does not contain "Android")
- **iOS/macOS link type**: extended `get_link_type()` to return `href` for
  iOS 9+ (except 10) and macOS 10.12+ including macOS 11–15
- **Cleanup**: removed unused `import requests`; removed dead `user_agent`
  parse in `android_cpa_needs_204_now()` (was parsed but never accessed)
