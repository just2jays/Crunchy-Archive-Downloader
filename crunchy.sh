#!/bin/bash
export PATH=/usr/local/bin:$PATH

function joinBands { perl -e '$s = shift @ARGV; print join($s, @ARGV);' "$@"; }

DIR=~/Music/live-music/*
for f in $DIR; do mv "$f" "${f// /_}"; done

url_list=""

read -d '' band_collections << EOF
Aqueous
ConsidertheSource
CosmicDustBunnies
DiscoBiscuits
Dopapod
Formula5
GratefulDead
HeavyPets
JoeRussosAlmostDead
KellerWilliams
KungFuband
lespecial
MaxCreek
MisterFMusic
moe
MunMusic
PhilLeshandFriends
PigeonsPlayingPingPong
Quactus
Spafford
StringCheeseIncident
TeaLeafGreen
TheBreakfast
TheMantras
thewerks
Twiddle
UmphreysMcGee
EOF

SCRIPT_DIR=~/Music/
DL_DIR=~/Music/live-music/
PRE='https://archive.org/advancedsearch.php?q=collection%3A%28'
MID=$(joinBands "+OR+" $band_collections)
#POST='%29&fl%5B%5D=identifier&fl%5B%5D=title&sort%5B%5D=addeddate+desc&sort%5B%5D=&sort%5B%5D=&rows=5&page=1&callback=callback&output=rss'
POSTCSV='%29&fl%5B%5D=identifier&fl%5B%5D=creator&sort%5B%5D=addeddate+desc&sort%5B%5D=&sort%5B%5D=&rows=5&page=1&callback=callback&save=yes&output=csv'

FETCHURL=$PRE$MID$POSTCSV

RESULT=$(wget -qO- "$FETCHURL")
wget -nd -q "$FETCHURL" -O $SCRIPT_DIR"identifiers.txt"
tail -n +2 $SCRIPT_DIR"identifiers.txt" | sed 's/"//g' > $SCRIPT_DIR"processedidentifiers.txt"

idents=()
for fn in `cat $SCRIPT_DIR"processedidentifiers.txt" | sed 's/ /_/g'`; do
    creator=${fn#*\,}
    identifier=${fn%%\,*}
    zip_url="https://archive.org/compress/$identifier/formats=VBR+MP3"
    full_creator=$(echo "$creator" | sed 's/_/ /g')

    if [ ! -d $DL_DIR$creator/$identifier ]; then
        idents+=$DL_DIR$creator/$identifier" "
        url_list+=$zip_url**$DL_DIR$creator" "
    else
        echo "|---------------------------------------|"
        echo "|  Show already downloaded - skipping!  |"
        echo "|---------------------------------------|"
    fi

done

echo $url_list | sed 's/\*\*/ --content-disposition -P /g' | xargs -n 4 -P 8 wget

for ident in $idents; do
    echo $ident
    unzip $ident.zip -d $ident
    rm $ident.zip
done

for f in $DIR; do mv "$f" "${f//_/ }"; done

echo "|---------------------------------------|"
echo "| Completed show downloads succesfully! |"
echo "|---------------------------------------|"
rm $SCRIPT_DIR"identifiers.txt"
rm $SCRIPT_DIR"processedidentifiers.txt"

exit;
