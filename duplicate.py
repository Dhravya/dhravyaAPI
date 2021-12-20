uniqlines = set(open("/var/www/api/dhravyaAPI/wyr.txt").readlines())

open("/var/www/api/dhravyaAPI/wyr.txt", "w").writelines(uniqlines)
