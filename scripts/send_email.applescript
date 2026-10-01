on run argv
    if (count of argv) is not 3 then error "Uso: osascript send_email.applescript destinatario assunto arquivo_texto"
    set destinationAddress to item 1 of argv
    set messageSubject to item 2 of argv
    set contentPath to POSIX file (item 3 of argv)
    set messageBody to read contentPath as «class utf8»
    tell application "Mail"
        set messageToSend to make new outgoing message with properties {subject:messageSubject, content:messageBody, visible:false}
        tell messageToSend
            make new to recipient at end of to recipients with properties {address:destinationAddress}
            send
        end tell
    end tell
end run
