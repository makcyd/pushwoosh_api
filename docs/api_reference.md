#Pushwoosh API

General
-------
* /getResults [+]


Messages
-------
* /createMessage [+]
* /cancelMessage
* /deleteMessage [+]
* /createTargetedMessage
* /getMessageDetails
* /getPushHistory [+]


Presets
-------
* /createPreset [+]
* /getPreset [+]
* /listPresets [+]
* /deletePreset [+]


Devices
-------
* /registerDevice [+]
* /unregisterDevice [+]
* /deleteDevice [+]
* /checkDevice
* /setBadge
* /applicationOpen
* /pushStat
* /messageDeliveryEvent
* /setPurchase
* /createTestDevice
* /listTestDevices


Tags
----
* /addTag [+]
* /deleteTag [+]
* /listTag [+]
* /getTag
* /setTags
* /bulkSetTags (async, getResults)


Filters
-------
* /createFilter [+]
* /listFilters [+]
* /deleteFilter [+]
* /exportSegment (async, getResults) [+]


User-Centric API
----------------
* /registerUser [+]
* /unregisterUser (undocumented)
* /getUsersDetails (async, getResults)


Events
------
* /createEvent


Applications
------------
* /createApplication
* /updateApplication
* /deleteApplication
* /getApplication
* /getApplications [+]
* /getApplicationFile
* /setApplicationPlatformStatus
* /configureApplication


Campaigns
---------
* /createCampaign
* /getCampaign
* /deleteCampaign


Geozones
--------
* /getNearestZone
* /addGeoZone
* /updateGeoZone
* /deleteGeoZone
* /addGeoZoneCluster
* /listGeoZones
* /listGeoZoneClusters


Email
-----
* /createEmailMessage
* /registerEmail
* /registerEmailUser
* /deleteEmail
* /setEmailTags
* /getBouncedEmails (async, getResults)


Inbox
-----
* /getInboxMessages [+]
* /inboxStatus


Statistics
----------
* /getMsgStats (async, getResults)
* /getMsgPlatformsStats (async, getResults)
* /getApplicationSubscribersStats 
* /getAppStats (async, getResults)
* /getCampaignStats (async, getResults)
* /getEventStatistics (async, getResults)
* /getTagStats (async, getResults)