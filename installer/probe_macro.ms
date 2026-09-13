macroScript NCFormatProbe category:"NC-Test"
(
    global gNCFP1 = "RAN-FILE-SCOPE"
    format "NCFP: body statement executed\n"
    rollout rltNCFP "probe"
    (
        label l1 "ok" pos:[5,5]
        on rltNCFP create do ( global gNCFP2 = "RAN-CREATE" )
    )
    on execute do ( format "NCFP: execute ran\n" )
)
