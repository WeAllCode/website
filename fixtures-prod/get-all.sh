#!/usr/bin/env bash

# To run:
# command time ./get-all.sh && say "I'm done."

models=(
    "sites.site"
    "auth.group"
    "socialaccount.socialapp"
    "redirects.redirect"
    "coderdojochi.cdcuser"
    "coderdojochi.course"
    "coderdojochi.equipmenttype"
    "coderdojochi.location"
    "coderdojochi.meetingtype"
    "coderdojochi.raceethnicity"
    "coderdojochi.guardian"
    "coderdojochi.meeting"
    "coderdojochi.mentor"
    "coderdojochi.student"
    "coderdojochi.session"
    "coderdojochi.mentororder"
    "coderdojochi.order"
    "weallcode.boardmember"
    "weallcode.associateboardmember"
    "weallcode.staffmember"
)

heroku run --app production-wac python -W ignore manage.py dumpdata "${models[@]}" -- >"all.json"
