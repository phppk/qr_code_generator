Lvl 3 ECL: L QR-Code Generator in Python

Dies ist ein Repository für einen QR-Code-Generator in python.

Der Scope dieses Generators beinhält nur einen Level 3 QR Code (Größe von 29x29 Pixel) mit dem Error Correction level L (Anzahl von Error Correction Codewords, L = LOW).

## How to Use

Dieser Generator hat eine GUI Komponente zur einfachen Nutzung des Generators.
Es muss lediglich die Datei [qr_tk_ui.py] ausgeführt werden.
- In dieser GUI muss der Nutzer einen String (Youtube Link, o.ä.) Eintragen.
- Der Output Pfad des QR-Codes ist automatisch vorausgefüllt, kann aber vom Nutzer beliebig geändert werden.
- Nach dem generieren erstellt die GUI eine Vorschau des Codes, sowie eine im gegebenen Pfad gespeicherte .png Datei.

## Dieser Generator ist in 4 Teile Aufgeteilt.

1. "qr_code_calc.py"
   - Konvertiert den Input-String in die Datenbits, die den Inhalt des QR-Codes ausmachen.
   - Der Input String wird in Bits und Bytes umgerecht, da der Byte-Mode genutzt wird.
   - Es werden Pad-Bytes hinzugefügt, wenn benötigt.
   - Mithilfe von Polynomdivison wird innerhalb von Galios Fields (255) die Datenkorrektur berechnet.
   - Am Ende dieses Datenstrings wird nun ein Terminator + Terminator angefügt, um alle benötigten 567 bits zu füllen.
2. "draw_qr_code.py"
   - Erstellt mithilfe von PIL (Python Image Library) einen QR-Code als Bildatei.
   - Es werden zuerst alle statischen Aspekte eines QR-Codes in einem Array hinterlegt.
   - Diese statischen Bits können und müssen nach dem ersten Einpflegen in das Array nicht geändert werden.
   - In die nun verbleibenden leeren Bits werden die vorher berechneten Datenbits eingepflegt.
3. "qr_tk_ui.py"
   - Eine GUI die den Nutzer nach einem Input String und Dateipfad fragt.
   - Dieser Input String wird verarbeitet und als Bilddatei als QR-Code im hinterlegeten Dateipfad gespeichert.
4. "variables.py"
   - Einige Hilfsvariablen für den qr code calculator und das draw module.
