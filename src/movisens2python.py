'''movisens2python'''
import os
from tkinter import filedialog, Tk
import xml.etree.ElementTree as et
import numpy as np
from matplotlib import pyplot as plt

# CLASSES


class Movisens():
    '''
    Basisklasse zum einlesen und bereitstellen von Movisens CSV Daten in Python
    '''
    # Verbesserungsmöglichkeiten:
    # - Daten schön machen inkl. Datasheet infos z.B CM = 560µV ECG
    # - NoData Option: Signale sollen nicht eingelesen werden aber dafür XML Info,
    #   dazuSignal getrennt einlesen,
    #   nachdem XML Info geladen bereis fertig geladen wurde: Extra Funktionen für Read
    #   dazu nötig: Subclassfunktion die den Parameter bearbeitet
    # - Default Ausgabe: Baumstruktur nur auch vorhandene Parameter,
    #   bei den Klassen werden alle Attribute angezeigt auch wenn nicht vorhanden
    # - Allgemeins Problem: Mögliche Leere Auswahlparameter bei verschiedenen Entrys
    # - z.B Evententry hat kein Attr. Signal, und nicht jeder Signalentry hat eine Baseline
    # - Zeitbereichsauswahl ermöglichen: Start und Dauer
    # - @propertys einführen für choosedata und customsettings
    # - Exits und Fehlermeldungen einbauen

    def __init__(self):
        '''Init der BaseClass Objektvariablen'''
        # Choosedata
        self.filename = None
        self.filepfad = None
        self.name = None
        # Customsettings
        self.start = None
        self.dauer = None
        self.readinlist = []
        self.defaultcontents = ['acc', 'angularrate', 'artifact', 'bpmbxb_live', 'charging', 'ecg', 'hr_live', 'hrvisvalid_live', 'hrvrmssd_live', 'marker',
                                'movementacceleration_live', 'nn_live', 'nnlist', 'press', 'stateofcharge', 'stepcount_live', 'temp', 'tempmean_live', 'eda',
                                'EMG1', 'EMG2', 'EMG3', 'EMG4', 'EMG5', 'EMG6', 'EMG7', 'EMG8', 'EEG3', 'EEG5', 'ECG6', 'seizures', 'm6seizures', 'm6emgseizures', 'bicepsseizures']

    def choose_data(self, extension='.xml', datatype='unisens'):
        '''Funktion zum Auswählen der Daten'''
        root = Tk()  # TinkerDialog öffnen
        root.withdraw()  # Tinkerfenster verstecken
        files = filedialog.askopenfilenames(
            defaultextension='.*',
            filetypes=[(datatype, extension), ],
            title="Select Files",
            multiple=True,
        )
        self.filepfad = os.path.dirname(files[0])
        if len(files) <= 1:
            self.filename = os.path.split(files[0])[1]
        else:
            self.filename = os.path.split(self.filepfad)[1]
        self.name = os.path.splitext(self.filename)[0]

    def set_customsettings(self, datenliste, start, dauer):
        '''Funktion zur Bearbeitung der Custom Input Parameter'''
        if not datenliste:
            self.readinlist = self.defaultcontents
        else:
            self.readinlist = datenliste

        self.start = start
        self.dauer = dauer

    def add_content(self, name):
        '''Funktion zum Hinzufügen von zusätzlichen Kanälen'''
        self.defaultcontents.append(name)

    def get_xml(self):
        '''Funktion zum Lesen der XML-Unisens Informationen '''

        # Namespace und Wurzel deklarieren
        unisensspace = {'uni': 'http://www.unisens.org/unisens2.0'}
        tree = et.parse(self.filepfad + '/' + self.filename)
        wurzel = tree.getroot()

        # RootAttributes
        self.rootinfo = RootAttributes()
        for key, val in wurzel.attrib.items():
            if hasattr(self.rootinfo, key):
                setattr(self.rootinfo, key, val)

        # CustomAttributes
        self.custominfo = CustomAttributes()
        for customatt in wurzel.findall(
                'uni:customAttributes/uni:customAttribute', namespaces=unisensspace):
            if hasattr(self.custominfo, customatt.attrib['key']):
                setattr(
                    self.custominfo, customatt.attrib['key'], customatt.attrib['value'])

        # SignalEntry
        for signal in wurzel.findall(
                'uni:signalEntry', namespaces=unisensspace):
            if signal.attrib['id'].split('.')[0] in self.readinlist:

                # Signaleintrag erstellen
                self.signal_entry = SignalEntry()

                # Attributes speichern
                for key, value in signal.attrib.items():
                    if hasattr(self.signal_entry, key):
                        setattr(self.signal_entry, key, value)

                # Channels speichern
                channellist = []
                for channel in signal.findall(
                        'uni:channel', namespaces=unisensspace):
                    channellist.append(channel.attrib['name'])
                setattr(self.signal_entry, 'channels', channellist)

                # Signaldatei einlesen
                # Prüfen ob Binary oder CSV
                if signal.attrib['id'].split('.')[1] == 'csv':
                    with open(str(self.filepfad + '/' + signal.attrib['id']), 'r') as csvfile:
                        read = np.genfromtxt(
                            csvfile, dtype=np.int, delimiter=';')
                        # csv nimmt automatisch richtige integersize
                        # damit alle gleiches Format haben
                        read = read.astype('int32')
                else:  # hier nochmal unterscheiden zwischen int16 und int32
                    if signal.attrib['dataType'] == 'int32':
                        with open(str(self.filepfad + '/' + signal.attrib['id']), 'rb') as binfile:
                            read = np.fromfile(binfile, dtype=np.int32)
                    else:
                        with open(str(self.filepfad + '/' + signal.attrib['id']), 'rb') as binfile:
                            read = np.fromfile(binfile, dtype=np.int16)
                            # damit alle gleiches Format haben
                            read = read.astype('int32')

                setattr(self.signal_entry, 'signal', read)

                # SignalEntry in Namen der jeweiligen CSV Datei umschreiben
                rename_attribute(self, 'signal_entry',
                                 signal.attrib['id'].split('.')[0])

        # ValuesEntry
        for values in wurzel.findall(
                'uni:valuesEntry', namespaces=unisensspace):
            if values.attrib['id'].split('.')[0] in self.readinlist:

                # Valueseintrag erstellen
                self.values_entry = ValuesEntry()

                # Attributes speichern
                for key, value in values.attrib.items():
                    if hasattr(self.values_entry, key):
                        setattr(self.values_entry, key, value)

                # Channels speichern
                channellist = []
                for channel in values.findall(
                        'uni:channel', namespaces=unisensspace):
                    channellist.append(channel.attrib['name'])
                setattr(self.values_entry, 'channels', channellist)

                # Valuesdatei einlesen
                # If not needed Values Entry only as CSV
                if values.attrib['id'].split('.')[1] == 'csv':
                    with open(str(self.filepfad + '/' + values.attrib['id']), 'r') as csvfile:
                        read = np.genfromtxt(
                            csvfile, dtype=np.uint, delimiter=';')
                        # read = list(csv.reader(csvfile, delimiter=';'))
                        # read = np.array(read[0:], dtype=np.int)

                setattr(self.values_entry, 'values', read)

                # ValuesEntry in Namen der jeweiligen CSV Datei umschreiben
                rename_attribute(self, 'values_entry',
                                 values.attrib['id'].split('.')[0])

        # EventEntry
        for event in wurzel.findall('uni:eventEntry', namespaces=unisensspace):
            if event.attrib['id'].split('.')[0] in self.readinlist:

                # Eventeintrag erstellen
                self.event_entry = EventEntry()

                # Attributes speichern
                for key, value in event.attrib.items():
                    if hasattr(self.event_entry, key):
                        setattr(self.event_entry, key, value)

                # Eventdatei einlesen
                with open(str(self.filepfad + '/' + event.attrib['id']), 'r') as csvfile:
                    event_time = []
                    event_typ = []
                    for row in csvfile:
                        event_time.append(row.strip().rsplit(';', 2)[0])
                        event_typ.append(row.strip().rsplit(';', 2)[1])
                setattr(self.event_entry, 'event',
                        np.asarray(event_time, dtype=np.int))
                setattr(self.event_entry, 'eventtyp',
                        np.asarray(event_typ, dtype='U10'))

                # EventEntry in Namen der jeweiligen CSV Datei umschreiben
                rename_attribute(self, 'event_entry',
                                 event.attrib['id'].split('.')[0])

    def get_entry(self, name):
        '''Funktion zur Herausgabe von Informationen eines bestimmten Entrytyps'''
        # SignalEntry
        subclassenobject = getattr(self, name)
        if isinstance(subclassenobject, SignalEntry):
            return subclassenobject
        # ValuesEntry
        elif isinstance(subclassenobject, ValuesEntry):
            return subclassenobject
        # EventEntry
        elif isinstance(subclassenobject, EventEntry):
            return subclassenobject


class RootAttributes(Movisens):
    '''RootAttributes'''

    def __init__(self):
        super().__init__
        self.duration = None
        self.measurementId = None
        self.timestampStart = None


class CustomAttributes(Movisens):
    '''CustomAttributes'''

    def __init__(self):
        super().__init__
        self.age = None
        self.gender = None
        self.height = None
        self.personId = None
        self.sectorCount = None
        self.sensorLocation = None
        self.sensorSerialNumber = None
        self.sensorType = None
        self.sensorVersion = None
        self.weight = None


class SignalEntry(Movisens):
    '''SignalEntry'''

    def __init__(self):
        super().__init__
        self.adcResolution = None
        self.baseline = None
        self.channels = []
        self.comment = None
        self.contentClass = None
        self.dataType = None
        self.id = None
        self.lsbValue = None
        self.sampleRate = None
        self.unit = None
        self.signal = None


class ValuesEntry(Movisens):
    '''ValuesEntry'''

    def __init__(self):
        super().__init__
        self.adcResolution = None
        self.baseline = None
        self.channels = []
        self.comment = None
        self.contentClass = None
        self.dataType = None
        self.id = None
        self.lsbValue = None
        self.sampleRate = None
        self.unit = None
        self.values = None


class EventEntry(Movisens):
    '''EventEntry'''

    def __init__(self):
        super().__init__
        self.commentLength = None
        self.id = None
        self.sampleRate = []
        self.typeLength = None
        self.event = None
        self.eventTyp = None

# HELPERFUNCTIONS


def rename_attribute(obj, old_name, new_name):
    '''Funktion zur Namensänderung eines eingelesen Kanals'''
    obj.__dict__[new_name] = obj.__dict__.pop(old_name)


# MAIN

def convert(*signal_types, **keywords):
    '''
    Funktion zur Erstellung eines Movisens Objekts

    Non-keyword Arguments
    Welche Signaleinträge gelesen werden sollen:
    *signaltypes = *args [string] [Default = None, entspricht All Data]
    'acc'
    'angularRate'
    'artifact'
    'bpmBxb_live'
    'charging'
    'ecg'
    'hr_live'
    'hrvIsValid_live'
    'hrvRmssd_live'
    'movementAcceleration_live'
    'marker'
    'nn_live'
    'press'
    'stateofCharge'
    'stepCount_live'
    'temp'
    'tempMean_live'

    Keyword Arguments
    **keyowrds = **kwargs [key = string] [Default = None]
    Wenn der XML Baum ausgegeben werden soll:
    showtree = True [Default = False]

    Falls extra weitere Markerdateien/Artifactsdateien genutzt werden:
    extrafile = 'dateiohnepostfix'

    Startzeipunkt der Analyse [ms]: Optional Parameter [string] [Default = None]
    start = 'YYYY-MM-DDThh:mm:ss.xxx'

    Dauer der Anlayse in [s]: Optional Parameter [float] [Default = None]
    dauer = 120123.0
    '''

    # Non-keyword Arguments listen
    data_list = []
    for arg in signal_types:
        data_list.append(arg)

    # Keyword Arguments listen

    # Times
    if 'start' not in keywords:
        start = None
    else:
        start = keywords['start']
    if 'dauer' not in keywords:
        dauer = None
    else:
        dauer = keywords['dauer']
    if 'extrafile' in keywords:
        extrafile = keywords['extrafile']
    else:
        extrafile = None

    # Objekt erstellen
    movisens_object = Movisens()
    # Daten auswhählen
    movisens_object.choose_data()
    # Funktion zum Hinzufügen von Extrafiles
    if extrafile is not None:
        movisens_object.add_content(extrafile)
    # Funktion zur Bearbeitung der Eingabeparameter
    movisens_object.set_customsettings(data_list, start, dauer)
    # XML einlesen
    movisens_object.get_xml()

    # XML Baum zeigen [Default None]
    if 'showtree' in keywords:
        if keywords['showtree'] is True:
            print('Movisensobjekt')
            for key in movisens_object.__dict__:
                if isinstance(movisens_object.__dict__[key],
                              (RootAttributes, CustomAttributes,
                               SignalEntry, ValuesEntry, EventEntry)):
                    print(f'-->{key}')
                    for ykey in movisens_object.__dict__[key].__dict__:
                        # if movisensobject.__dict__[key].__dict__[ykey] !=
                        # None:
                        print(f'-----{ykey}')
                else:
                    # if movisensobject.__dict__[key]:
                    print(f'-----{key}')

    return movisens_object


if __name__ == '__main__':

    '''
    EXAMPLE

    (1) Erstellung eines Movisens Objekts mit allen Signalen, die verfügbar sind

    (2) ECG Signalwerte mit LsbValue und Baseline umrechnen

    (3) ECG Signal im Bereich von 10 -20 Sekunden plotten

    '''

    # Objekt erstellen, mit Signaltyp ECG
    movisens_example = convert(showtree=True)

    # SignalEntry ECG und ValuesEntry NN_Live auslesen
    ecg = movisens_example.get_entry('ecg')
    ecg_signal = (ecg.signal - int(ecg.baseline)) * float(ecg.lsbValue)
    ecg_fs = ecg.sampleRate

    # PLOT ECG
    plt.plot(ecg_signal, label='ECG Signal')

    # PLOT Settings
    plt.title('ECG Single Lead movisens ecgMove4 Chest', fontweight="bold")
    plt.xlabel(f'Samples @ {ecg_fs} ')
    plt.ylabel(f'Amplitude in {ecg.unit} ')

    # Bereiche 10-20 Sekunden
    plt.xlim(10 / (1 / int(ecg_fs)), 20 / (1 / int(ecg_fs)))
    plt.legend(loc='upper right')
    plt.show()
