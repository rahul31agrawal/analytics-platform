BUILD_ROOT=$(pwd)
echo $BUILD_ROOT
ls $BUILD_ROOT
touch superset/build_docker
BUILD_FOLDER=$BUILD_ROOT

cd $BUILD_FOLDER

FOLDERS=(
  'superset/common/'
  'superset/connectors/'
  'superset/connectors/base/'
  'superset/connectors/druid/'
  'superset/connectors/iou/'
  'superset/connectors/sqla/'
  'superset/db_engine_specs/'
  'superset/db_engines/'
  'superset/iou/'
  'superset/migrations/'
  'superset/models/'
  'superset/models/sql_types/'
  'superset/tasks/'
  'superset/translations/'
  'superset/utils/'
  'superset/views/'
  'superset/views/database/'
  'superset/views/log/'
)

for FOLDER in "${FOLDERS[@]}"
do
  echo "Running build for :"$FOLDER

  EXCLUSION='__init__.py'
  if [ "$FOLDER" == 'superset/utils/' ] || [ "$FOLDER" == 'superset/views/' ];
  then
    EXCLUSION=$EXCLUSION'\|core.py'
  elif [ "$FOLDER" == 'superset/connectors/base/' ] || [ "$FOLDER" == 'superset/connectors/druid/' ] || [ "$FOLDER" == 'superset/connectors/sqla/' ];
  then
    EXCLUSION=$EXCLUSION'\|models.py'
  elif [ "$FOLDER" == 'superset/db_engine_specs/' ];
  then
    EXCLUSION=$EXCLUSION'\|base.py'
  fi
  echo "Exclusion :"$EXCLUSION
  FILES=$(ls $BUILD_FOLDER/$FOLDER/*.py | grep -v $EXCLUSION)
  FILES_ARRAY=($FILES)
  cd $BUILD_FOLDER/$FOLDER && ls
  cd $BUILD_FOLDER/$FOLDER && easycython --no-annotation $FILES
  for F in "${FILES_ARRAY[@]}"
  do
    if [[ "$F" != *__init__.py ]];
    then
      FILE_NAME="${F%.*}"
      FILE=$(ls $FILE_NAME.*.so)
      if [[ "$FILE" == $FILE_NAME.*.so ]];
      then
        rm -rf $BUILD_FOLDER/$FOLDER/build
        rm $FILE_NAME.py
        rm $FILE_NAME.c
      fi
    fi
  done
done



