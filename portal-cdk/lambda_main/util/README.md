# Notifications

The notifications system is broadly divided into three different parts:

- [Google Calendar](#adding-event-to-calendar)
- [Notification URL](#getting-events-via-portal-url)
- [Notification page hooks](#adding-notification-hook-to-page)

## Adding event to calendar

### Create Google Calendar event

Create Calendar event in Google Calendar. The calendar must be public with a publicly available ICAL-compatible URL.
By default, calendars should be by maturity. The production calendar should be used by the all production portal and labs.

### Event schema

#### Event Title

The event title will be placed as the title of the event in the popup toast.

#### Event Dates

The event dates will be based on the calendar. Times will be parsed as UTC.

#### Event Description

The event description contains two sections: meta and message.

1. The meta section tells the poral where and how to show the message.
2. The message can be any HTML compatible text. It will be the main message within the toast.

> [!NOTE]
> Note that Google Calendar wants to automagically make hyperlinks linkable. That means that any hyperlinks will need to be delinked before saving changes. Otherwise, hyperlinks will not work as expected.
>
> [!TIP]
> Make it easier on users by coloring blue any hyperlink text. This can be accomplished via adding `<span style="color: blue"></span>`.
>
> [!TIP]
> Open hyperlinks into another browser tab via `target="_blank"`.
>
> [!IMPORTANT]
> The placement of the multiple toasts might not have the expected behavior. The first toast render on the page will determine the position of subsequent toasts irrespective of how they are defined in the event meta. Therefore, it might be more prudent to decide early on where the toasts will be stacked.

```yaml
---
scopes: scope1, scope2
tags: tag1, tag2, all
type: info | success | error | warning
placement: top-right | bottom-right | bottom-left | top-left | top-full-width | bottom-full-width | top-center | bottom-center
---
<p> This is a message </p>

<p>This is a <a href="#" target="_blank">
    <span style="color: blue">
        link
    </span>
</a>
```

`scopes`: Comma-seperated string with values of `portal` or the lab short name of the cluster.

`tags`: Comma-seperated string represents the location/page where to show the notifications. The special value `all` means provide all available profiles.

`type`: String giving status of toast: `info` (blue) | `success` (green) | `error` (red) | `warning` (yellow).

`placement`: String giving placement of toast. See example above for options.

### Calendar URL environment variable

The public calendar URL will need to be added to the build via the `CALENDAR_URL` environment variable.

For local builds, this can be accomplished by setting `CALENDAR_URL` within your [Makefile](../../../Makefile#L94) environment for `make cdk-shell`.

For GitHub builds, `CALENDAR_URL` within GitHub Actions is set from {repo} > `Settings` > `Environments` > {maturity} > `Environment variables`.

Note the Test Calendar URL is hardcoded as a default within [Makefile](../../../Makefile#L43).

## Getting events via portal URL

When properly configured, the events for a particular `scope` and `tag` can be found via the path GET `/notifications/{scope}?tag={tag}`. If `tag` is not included or if `tag` has the special value `all` then all possible tags for that scope will be used.

The returned object is a json dictionary of the example format

```json
[
  {
    "title": "Calendar Event Title",
    "message": "Calendar Event Description",
    "type": "info",
    "placement": "top-full-width"
  }
]
```

This format is easy for the javascript toast library to parse and use.

> [!WARNING]
> For reverse compatibility with systems that expect Portal v1, the path schema `/user/notifications/{lab_short_name}?profile={profile}` is also provided. This is to be considered deprecated.

## Adding notification hook to page

Within the portal, [notifications.j2](../../../portal-cdk/lambda_main/templates/notifications.j2) provides the needed javascript and css methods for the toast to work. To use the notifications jinja template, within another jinja template add the following:

```jinja
{% with -%}
    {% set scope = "scope" %}
    {% set tag = "tag" %}
    {% include 'notifications.j2' %}
{% endwith -%}
```

[Example code](../../../portal-cdk/lambda_main/templates/portal.j2#L7)
