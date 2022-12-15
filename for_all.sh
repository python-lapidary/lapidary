for dir in ./*/
do
    dir=${dir%*/}
    (cd "${dir##*/}"; $@)
done
