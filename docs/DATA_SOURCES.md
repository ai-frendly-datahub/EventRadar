# EventRadar Data Source Research Report

**Generated:** 2026-03-04  
**Research Duration:** 5m 17s

---

## RSS FEEDS (20+ Sources)

### Exhibition & Trade Show RSS Feeds

1. **ACT Expo RSS Feed** - `https://www.actexpo.com/feed/`
   - Category: Transportation technology trade show
   - Quality: High

2. **ECOC Exhibition RSS Feed** - `https://www.ecocexhibition.com/exhibitor-news/feed/`
   - Category: Optical communications exhibition (Europe)
   - Quality: High

3. **UFI Blog RSS Feed** - `https://blog.ufi.org/feed/`
   - Category: Global exhibition industry association
   - Quality: High

4. **IAEE Blog RSS Feed** - `https://www.iaee.com/feed/`
   - Category: International Association of Exhibitions and Events
   - Quality: High

5. **Exhibitor Magazine RSS Feed** - `http://www.exhibitoronline.com/r630/ExhibitorNewsNetwork.xml`
   - Category: Trade show and corporate event marketing
   - Quality: High

6. **Event Marketer RSS Feeds** - `https://www.eventmarketer.com/rss-feeds-list/`
   - Categories: All, Business, Events, Technology
   - Quality: High

7. **IWPC Industry Calendar RSS** - `https://iwpc.org/SearchCalendar.aspx/rss.xml`
   - Category: Industry conference and workshop calendar
   - Quality: Medium

### Museum & Venue RSS Feeds

8. **Museen Basel Events RSS** - `https://opendata.swiss/en/dataset/events-museen-basel-rss-feed`
   - Category: Museum events in Basel, Switzerland
   - Quality: High (Open Data)

---

## APIs (8+ Sources)

### Eventbrite API
**Base URL**: `https://www.eventbriteapi.com/v3/`  
**Documentation**: https://www.eventbrite.com/platform/api/

**Key Endpoints**:
- GET Events: `GET https://www.eventbriteapi.com/v3/organizations/{organization_id}/events/`
- GET Event Details: `GET https://www.eventbriteapi.com/v3/events/{event_id}/`

**Authentication**: OAuth 2.0 Bearer token  
**Quality**: High (Official API)

### Ticketmaster Discovery API
**Base URL**: `https://app.ticketmaster.com/discovery/v2/`  
**Documentation**: https://developer.ticketmaster.com/products-and-docs/apis/getting-started/

**Key Endpoints**:
- Search Events: `https://app.ticketmaster.com/discovery/v2/events.json?apikey={apikey}`
- Event Details: `https://app.ticketmaster.com/discovery/v2/events/{id}.json?apikey={apikey}`
- Venue Search: `https://app.ticketmaster.com/discovery/v2/venues.json?apikey={apikey}`

**Authentication**: API Key as query parameter  
**Rate Limit**: 5,000 calls/day, 5 requests/second (default)  
**Quality**: High (Official API)

### Meetup GraphQL API
**Base URL**: `https://www.meetup.com/api/graphql`  
**Documentation**: https://www.meetup.com/api/schema/

**Key Queries**:
- Get Event: `event(id: ID) { title, description, dateTime }`
- Search Events: `keywordSearch(input: ConnectionInput)`
- Group Events: `groupByUrlname(urlname: String)`

**Authentication**: OAuth 2.0 (Pro subscription required)  
**Quality**: High (Official API)

### Korean Government APIs

1. **전국문화축제표준데이터 (National Cultural Festival Data)**
   - URL: https://www.data.go.kr/data/15013104/standard.do
   - Provider: Ministry of Culture, Sports and Tourism
   - Update: Quarterly
   - Fields: Festival name, location, start/end dates, content, organizer, coordinates

2. **서울시 문화행사 정보 (Seoul Cultural Events)**
   - URL: https://data.seoul.go.kr/dataList/OA-15486/S/1/datasetView.do
   - Source: Seoul Culture Portal (https://culture.seoul.go.kr)
   - Update: Daily
   - Fields: Category, district, event name, venue, dates, fees, performers, program, coordinates

3. **VISIT SEOUL API**
   - Base URL: https://api.visitseoul.net/contents/standard/list
   - Categories: Culture, Shopping, Festivals/Events/Performances

4. **한국영상물등급위원회 - Foreign Performance Recommendation Service**
   - URL: https://www.data.go.kr/en/data/15127680/openapi.do
   - Provider: Korea Media Rating Board
   - Data: Foreign/domestic performance recommendations

---

## WEB SCRAPING TARGETS (10+ Sites)

### Venue & Convention Center Calendars

1. **EverOut Seattle - Convention/Expo** - `https://everout.com/seattle/events/?category=community-convention-expo`
   - Type: Event listing with category filtering

2. **Greater Tacoma Convention Center** - `https://tacomaconventioncenter.org/event-calendar`
   - Type: Venue event calendar

3. **Visit Pierce County Events** - `https://www.visitpiercecounty.com/events/`
   - Type: Regional tourism events calendar

### Museum & Exhibition Calendars

4. **National Gallery of Art Calendar** - `https://www.nga.gov/calendar`
   - Type: Museum exhibitions and events

5. **National Museum of American History** - `https://americanhistory.si.edu/press/releases/March-2026-calendar`
   - Type: Museum events and exhibitions

### Korean Cultural Sites

6. **Korea Stage Festa** - `https://kstagefesta.kr/eng/`
   - Type: Nationwide performing arts festivals and events

### Conference & Event Discovery Platforms

7. **confs.tech** - Tech conference directory
   - Used by: Tech Events Intelligence Aggregator (Apify)

8. **Luma** - Event discovery platform
   - Used by: Multiple aggregators

---

## GITHUB EXAMPLES

### Official SDKs & Libraries

**Eventbrite Python SDK**
- Repo: https://github.com/eventbrite/eventbrite-sdk-python
- License: Apache-2.0
- Status: Last generated 2015 (may need updates)

### Event Aggregation Projects

1. **Tech Events Intelligence Aggregator** (Apify Actor)
   - Repo: taroyamada/tech-events-intelligence
   - Sources: confs.tech, Luma, Eventbrite
   - Features: Deduplication, unified event calendar
   - Pricing: $12/1,000 events

2. **Event Scraper Pro** (Apify Actor)
   - Repo: barrierefix/event-scraper-pro
   - Sources: Eventbrite, Meetup, Lu.ma
   - Features: RSVP counts, organizer intelligence, smart deduplication
   - Rating: 5.0 (2 reviews)

3. **Music Festival Scraper** (Apify Actor)
   - Repo: urban_quidnunc/music-festival-scraper
   - Scope: Worldwide music festivals
   - Features: Lineups, dates, ticket info

4. **Conference & Event Scraper** (Apify Actor)
   - Repo: lanky_quantifier/conference-event-scraper
   - Features: Speaker info, schedules, pricing, attendee insights
   - Pricing: $3/1,000 results

### Educational Projects

**Event-Aggregation-and-Management-Platform**
- Repo: KevChen2003/Event-Aggregation-and-Management-Platform
- Stack: Python (Scrapy), MongoDB
- Features: Computer science conferences, email notifications, Google Calendar integration

**roksme - Event Scraper & Aggregator**
- Repo: rossgrady/roksme
- Language: Python (94.6%)
- Generates: http://roks.me

---

## IMPLEMENTATION RECOMMENDATIONS

### Priority Tier 1 (Immediate Integration)
1. **Eventbrite API** - Most comprehensive, 700K+ event creators
2. **Ticketmaster Discovery API** - 230K+ events, good rate limits
3. **Korean Cultural Festival API** - Local data source, official
4. **Seoul Cultural Events API** - Daily updates, comprehensive local data

### Priority Tier 2 (Good Expansion)
5. **Meetup GraphQL API** - If Pro subscription available
6. **RSS Feeds** - 20+ exhibition/museum blogs for content discovery
7. **Venue Calendars** - Convention centers, museums (scraping required)
8. **VISIT SEOUL API** - Tourism events with rich metadata

### Priority Tier 3 (Future Enhancement)
9. **Apify Actors** - For multi-platform aggregation
10. **confs.tech/Luma** - For tech conference specialization
11. **International sources** - OpenData portals (Swiss museums, etc.)

### Technical Considerations

**Rate Limits**:
- Eventbrite: Documented in response headers
- Ticketmaster: 5,000 calls/day default
- Meetup: Pro subscription required

**Data Deduplication**:
- Events often appear on multiple platforms
- Use fuzzy matching (as demonstrated in Event Scraper Pro)
- Track seen events via state persistence

**Authentication**:
- Eventbrite: OAuth 2.0 Bearer token
- Ticketmaster: API key in query parameter
- Meetup: OAuth 2.0 (Pro only)
- Korean APIs: Usually API key or OAuth

**Content Types**:
- APIs return structured JSON (best)
- RSS feeds need parsing (moderate)
- Web scraping requires maintenance (high)

**Total Sources**: 20+ RSS, 8+ APIs, 10+ Scraping Targets
