
# Architectural considerations
* For the first iteration of this application, we'll store data files on disk where the app is running. In the future, for a more robust deployment, we'll switch to storing data files on S3. Do not implement S3 storage until explicitly notified to do so.
* RSS feeds should not be dynamically generated when they are requested. A request for an RSS feed should serve (or HTTP Redirect to) an existing file that contains the RSS feed.
* There will be a background batch job that refreshes each of the RSS feeds. This job should enumerate 

# ARCHITECTURE.md: Project Architecture Overview

This document outlines the high-level architecture, design patterns, and constraints for the project. Its purpose is to provide the AI agent (Claude) and human contributors with a clear understanding of how the system is organized.

## 1. Project Goal
* Primary Objective: Provide RSS feeds so users can subscribe to Avalanche forecasts via their prefered RSS reader.
* Target Audience: Backcountry users interested in regular updates on snowpack conditions.


## 2. High-Level System Overview
All content served to users will be static. RSS feeds will not change more than once a day, and the homepage enumerating avalache centers and zones will change less than once a year. As such, these will be generated offline, and user requests will receive a copy of html/rss/etc that was previously generated.

* Frontend: A single page pure HTML file (not a SPA, but single html file). This page is generated, but not on every request. It will change exceedingly infrequently so we can server it to users as a static file and can be checked into source control. There should be a tool/script which can re-generate this file. Use a Python library to generate this file from a tempate to html.
* Backend: A flask app that serves our previously generated content.
* Database: None needed

## 3. Key Architectural Patterns & Decisions
*   **Avalanche Center Storage:**
    *   *Rule:* A single YAML file checked into source control that enumerates each avalanche center, their name, a shortcode for the center that can be embeded into URLs and paths to files.
    *   *Rule:* You should generate the initial version of this file once, and after that it should never be changed by you without explicit permission from me.

*   **Zone Forecast Storage:**
    *   *Rule:* When a new forecast is obtained for a zone, it should be saved to disk in the format it was received (JSON I believe). The file should be stored in a heirarchical directory structure contain key metadata about the forecast. For example, "./forecasts/{avy_center_name}/{zone_name}/{year-month}/{year-month-day}/{avi_center_name-zone_name-year-month-day}-avalanche-forecast.json". Note this specific format isn't necessarily meant to be prescriptive, but to illusrate metadata that should be included. If a different format (say dates before avy center/zone) would work better for our RSS generation process, suggest such changes.

*   **Zone RSS Feed:**
    *   *Rule:* RSS feeds for each zone will consist of the last 10 forecast for the zone, transformed from the machine readable JSON format into a user presentable format. This transformation will happen offline.


## 4. Codebase Structure & Codemap

* /bin: a directory containing adhoc scripts, including tools for manually updating forecasts and/or generating rss feeds. These should be checked into source control
* /forecasts: a directory containing past avalache forecasts. These should not be checked into source control.
* /feeds: a directory containing rss feeds generated from forecasts
* /app: source code for the flask app, checked into source control
* /venv: a virtualenv for development, not checked into source control

