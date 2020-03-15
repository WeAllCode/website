#/bin/env bash

# To run:
# docker-compose run --rm app bash ./fixtures/get.sh
#

models=(
    "sites.site"
    "auth.group"
    "socialaccount.socialapp"
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
)

for i in "${!models[@]}"
do
    echo "Exporting '${models[$i]}' to '`printf %02d $i`-${models[$i]}.json'"
    python -W ignore manage.py dumpdata "${models[$i]}" --indent 2 > "fixtures/`printf %02d $i`-${models[$i]}.json"
done
