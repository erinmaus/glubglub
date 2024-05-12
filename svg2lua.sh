BASEDIR=$(dirname $0)
source $BASEDIR/venv/bin/activate
#python3 $BASEDIR/svg2lua.py $1 $2 2&> $1.log
python3 $BASEDIR/svg2lua.py $1 $2
if [ "$?" -ne "0" ]; then
    echo "svg2lua failed for $1"
fi
