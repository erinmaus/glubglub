BASEDIR=$(dirname $0)
source $BASEDIR/venv/bin/activate
python3 $BASEDIR/glubglub.py $1 $2 2&> $1.log
if [ "$?" -ne "0" ]; then
    echo "glubglub failed for $1"
fi
