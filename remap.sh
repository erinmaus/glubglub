BASEDIR=$(dirname $0)
source $BASEDIR/venv/bin/activate
python3 $BASEDIR/remap.py $@
if [ "$?" -ne "0" ]; then
    echo "remap failed for $1"
fi
