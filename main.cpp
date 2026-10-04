#include <QtWidgets>
#include <QtDBus>
#include <QtNetwork>
#include <functional>

static const QString portalService = "org.freedesktop.portal.Desktop";
static const QString portalPath = "/org/freedesktop/portal/desktop";
static const QString portalInterface = "org.freedesktop.portal.RemoteDesktop";
static const QString component = "voice-input";

class VoiceInput : public QWidget {
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "local.voiceinput.Controller")
public:
    VoiceInput() : recorder(this), worker(this), maxRecording(this), workerTimeout(this) {
        setWindowTitle(QStringLiteral("ورودی صوتی فارسی"));
        setLayoutDirection(Qt::RightToLeft);
        resize(600, 600);
        auto *layout = new QVBoxLayout(this);
        auto *heading = new QLabel("<h2>ورودی صوتی در برنامه‌ها</h2>");
        layout->addWidget(heading);
        auto *help = new QLabel(QStringLiteral(
            "۱. مجوز صفحه‌کلید را فعال کنید و این پنجره را ببندید.\n"
            "۲. داخل کادر متنِ برنامهٔ مقصد کلیک کنید.\n"
            "۳. Ctrl+Alt+W: شروع؛ دو ثانیه سکوت: پایان خودکار.\n"
            "همان میانبر برای پایان دستی هم کار می‌کند.\n"
            "Ctrl+Alt+Escape: لغو ضبط یا پردازش.\n"
            "تا درج متن، کادر مقصد را عوض نکنید.\n"
            "در ترمینال، حالت Ctrl+Shift+V را از منوی کنار ساعت انتخاب کنید."));
        help->setWordWrap(true);
        layout->addWidget(help);
        status = new QLabel;
        status->setWordWrap(true);
        layout->addWidget(status);
        auto *setup = new QPushButton(QStringLiteral("فعال‌کردن مجوز صفحه‌کلید"));
        connect(setup, &QPushButton::clicked, this, &VoiceInput::Setup);
        layout->addWidget(setup);
        preview = new QPlainTextEdit;
        preview->setReadOnly(true);
        preview->setPlaceholderText(QStringLiteral("آخرین متن در همین نشست؛ پردازش کاملاً محلی است"));
        auto *tabs = new QTabWidget;
        tabs->addTab(preview, QStringLiteral("متن اصلاح‌شده"));
        rawPreview = new QPlainTextEdit;
        rawPreview->setReadOnly(true);
        tabs->addTab(rawPreview, QStringLiteral("متن خام"));
        layout->addWidget(tabs);
        correctionSummary = new QLabel;
        correctionSummary->setWordWrap(true);
        layout->addWidget(correctionSummary);
        auto *copy = new QPushButton(QStringLiteral("کپی آخرین متن"));
        connect(copy, &QPushButton::clicked, this, [this] { setClipboard(lastText); });
        layout->addWidget(copy);
        auto *copyRaw = new QPushButton(QStringLiteral("کپی متن خام"));
        connect(copyRaw, &QPushButton::clicked, this, [this] { setClipboard(rawText); });
        layout->addWidget(copyRaw);
        auto *dictionaryButton = new QPushButton(QStringLiteral("واژه‌ها و اصلاحات شخصی"));
        connect(dictionaryButton, &QPushButton::clicked, this, &VoiceInput::editDictionary);
        layout->addWidget(dictionaryButton);
        auto *hideButton = new QPushButton(QStringLiteral("رفتن به کنار ساعت"));
        connect(hideButton, &QPushButton::clicked, this, &QWidget::hide);
        layout->addWidget(hideButton);
        QPixmap icon(64, 64); icon.fill(Qt::transparent);
        QPainter painter(&icon); painter.setRenderHint(QPainter::Antialiasing);
        painter.setPen(Qt::NoPen); painter.setBrush(QColor("#3867d6")); painter.drawEllipse(2, 2, 60, 60);
        painter.setBrush(Qt::white); painter.drawRoundedRect(25, 12, 14, 27, 7, 7);
        painter.setPen(QPen(Qt::white, 4)); painter.drawArc(18, 21, 28, 26, 180*16, 180*16);
        painter.drawLine(32, 45, 32, 52); painter.drawLine(24, 53, 40, 53); painter.end();
        setWindowIcon(QIcon(icon));
        tray = new QSystemTrayIcon(QIcon(icon), this);
        auto *menu = new QMenu(this);
        menu->addAction(QStringLiteral("نمایش تنظیمات"), this, &VoiceInput::Show);
        menu->addAction(QStringLiteral("فعال‌کردن مجوز صفحه‌کلید"), this, &VoiceInput::Setup);
        auto *terminal = menu->addAction(QStringLiteral("چسباندن در ترمینال (Ctrl+Shift+V)"));
        terminal->setCheckable(true);
        terminalMode = settings.value("terminalMode", false).toBool();
        terminal->setChecked(terminalMode);
        connect(terminal, &QAction::toggled, this, [this](bool on) {
            terminalMode = on; settings.setValue("terminalMode", on);
        });
        auto *engine = menu->addAction(QStringLiteral("موتور FastConformer فارسی"));
        engine->setCheckable(true);
        engine->setChecked(settings.value("fastconformer", true).toBool());
        connect(engine, &QAction::toggled, this, [this](bool enabled) { settings.setValue("fastconformer", enabled); });
        auto *spelling = menu->addAction(QStringLiteral("اصلاح محافظه‌کارانهٔ واژه‌ها"));
        spelling->setCheckable(true);
        spelling->setChecked(settings.value("correctSpelling", true).toBool());
        connect(spelling, &QAction::toggled, this, [this](bool on) { settings.setValue("correctSpelling", on); });
        menu->addAction(QStringLiteral("واژه‌ها و اصلاحات شخصی"), this, &VoiceInput::editDictionary);
        menu->addAction(QStringLiteral("لغو"), this, &VoiceInput::Cancel);
        menu->addSeparator();
        menu->addAction(QStringLiteral("خروج"), qApp, &QCoreApplication::quit);
        tray->setContextMenu(menu);
        connect(tray, &QSystemTrayIcon::activated, this, [this](QSystemTrayIcon::ActivationReason why) {
            if (why == QSystemTrayIcon::Trigger) Show();
        });
        tray->show();
        maxRecording.setSingleShot(true);
        connect(&maxRecording, &QTimer::timeout, this, &VoiceInput::Toggle);
        workerTimeout.setSingleShot(true);
        connect(&workerTimeout, &QTimer::timeout, this, [this] {
            worker.kill(); busy = false; cleanup(); report(QStringLiteral("زمان پردازش بیش از حد شد؛ دوباره تلاش کنید."));
        });
        connect(&recorder, &QProcess::readyReadStandardOutput, this, [this] { recorder.readAllStandardOutput(); });
        connect(&recorder, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
            if (error == QProcess::FailedToStart) {
                recording = false; maxRecording.stop(); cleanup();
                report(QStringLiteral("راه‌اندازی میکروفون شکست خورد: ") + recorder.errorString());
            }
        });
        connect(&recorder, qOverload<int,QProcess::ExitStatus>(&QProcess::finished), this,
                [this](int code, QProcess::ExitStatus exitStatus) {
            if (recording && code == 0 && exitStatus == QProcess::NormalExit) {
                recording = false; busy = true; maxRecording.stop();
                report(QStringLiteral("پایان گفتار تشخیص داده شد؛ در حال تبدیل به متن…"));
                transcribe();
            } else if (recording) {
                recording = false; maxRecording.stop(); cleanup();
                report(QStringLiteral("ضبط متوقف شد: ") + QString::fromUtf8(recorder.readAllStandardError()));
            } else if (sendAfterStop) {
                sendAfterStop = false;
                transcribe();
            } else cleanup();
        });
        connect(&worker, &QProcess::readyReadStandardOutput, this, &VoiceInput::readWorker);
        connect(&worker, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
            if (error == QProcess::FailedToStart) {
                busy = false; workerTimeout.stop(); cleanup(); report(worker.errorString());
            }
        });
        connect(&worker, qOverload<int,QProcess::ExitStatus>(&QProcess::finished), this,
                [this](int, QProcess::ExitStatus) {
            if (busy) {
                busy = false; workerTimeout.stop(); cleanup();
                report(QStringLiteral("پردازش گفتار متوقف شد: ") + QString::fromUtf8(worker.readAllStandardError()).right(800));
            }
        });
        // Drain diagnostics continuously to avoid filling the worker's pipe.
        connect(&worker, &QProcess::readyReadStandardError, this, [this] {
            diagnostics = (diagnostics + worker.readAllStandardError()).right(4096);
        });
        shortcutsReady = registerShortcuts();
        report(shortcutsReady ? QStringLiteral("میانبر آماده؛ مجوز صفحه‌کلید را فعال کنید.")
                              : QStringLiteral("ثبت میانبر KDE ناموفق بود؛ خروجی برنامه را بررسی کنید."));
    }
    ~VoiceInput() override {
        recording = false; sendAfterStop = false; busy = false;
        recorder.kill(); recorder.waitForFinished(2000);
        worker.kill(); worker.waitForFinished(2000); cleanup(); closeSession();
        QDBusInterface accel("org.kde.kglobalaccel", "/kglobalaccel", "org.kde.KGlobalAccel");
        for (const auto &id : {QString("toggle"), QString("cancel")})
            accel.call("setInactive", actionId(id));
    }
public slots:
    Q_SCRIPTABLE void Show() { show(); raise(); activateWindow(); }
    Q_SCRIPTABLE void Quit() { qApp->quit(); }
    Q_SCRIPTABLE QVariantMap GetStatus() const {
        return {{"keyboardReady", keyboardReady}, {"shortcutsReady", shortcutsReady},
                {"recording", recording}, {"processing", busy}, {"status", status->text()},
                {"lastText", lastText}, {"backend", backend}, {"diagnostics", QString::fromUtf8(diagnostics)}};
    }
    Q_SCRIPTABLE void Setup() {
        if (keyboardReady || setupBusy) return;
        setupBusy = true;
        report(QStringLiteral("منتظر مجوز KDE برای درج متن…"));
        request("CreateSession", {}, {{"session_handle_token", token()}}, 1);
    }
    Q_SCRIPTABLE void Toggle() {
        if (busy) { report(QStringLiteral("در حال پردازش؛ برای لغو Ctrl+Alt+Escape بزنید.")); return; }
        if (recording) {
            recording = false; sendAfterStop = true; busy = true;
            maxRecording.stop(); report(QStringLiteral("در حال تبدیل گفتار به متن…"));
            const auto stoppedPid = recorder.processId();
            recorder.terminate();
            QTimer::singleShot(1500, this, [this, stoppedPid] {
                if (recorder.state() != QProcess::NotRunning && recorder.processId() == stoppedPid) recorder.kill();
            });
            return;
        }
        if (recorder.state() != QProcess::NotRunning) return;
        if (!keyboardReady) { report(QStringLiteral("ابتدا مجوز صفحه‌کلید را از تنظیمات فعال کنید.")); return; }
        const QString python = QDir::homePath() + "/.local/share/whisper/venv/bin/python";
        if (!QFile::exists(python) || QStandardPaths::findExecutable("parec").isEmpty()) {
            report(QStringLiteral("Whisper یا ابزار ضبط parec پیدا نشد.")); return;
        }
        audio.reset(new QTemporaryFile(QDir::tempPath() + "/voice-input-XXXXXX.pcm"));
        if (!audio->open()) { report(QStringLiteral("ایجاد فایل موقت ناموفق بود.")); return; }
        rawPath = audio->fileName(); audio->close();
        recorder.start(python, {QCoreApplication::applicationDirPath() + "/capture.py", "--output", rawPath});
        recording = true;
        maxRecording.start(60000);
        report(QStringLiteral("● در حال ضبط؛ پایان خودکار پس از دو ثانیه سکوت"));
    }
    Q_SCRIPTABLE void Cancel() {
        ++pasteGeneration;
        recording = false; busy = false; sendAfterStop = false;
        maxRecording.stop(); workerTimeout.stop();
        recorder.kill(); worker.kill();
        recorder.waitForFinished(1000); worker.waitForFinished(1000);
        workerBuffer.clear(); cleanup(); report(QStringLiteral("لغو شد؛ آماده."));
    }
    Q_SCRIPTABLE bool TranscribeTestFile(const QString &path) {
        if (!keyboardReady || busy || recording) return false;
        QFile input(path);
        if (!input.open(QIODevice::ReadOnly) || input.size() < 32000 || input.size() > 1920000) return false;
        audio.reset(new QTemporaryFile(QDir::tempPath() + "/voice-input-XXXXXX.pcm"));
        if (!audio->open()) return false;
        if (audio->write(input.readAll()) != input.size()) { cleanup(); return false; }
        rawPath = audio->fileName(); audio->close();
        busy = true; transcribe(); return true;
    }
    // Explicit diagnostic command: caller selects a test field within three seconds.
    Q_SCRIPTABLE bool TestPaste(const QString &text) {
        if (!keyboardReady || busy || recording) return false;
        const auto generation = pasteGeneration;
        QTimer::singleShot(3000, this, [this,text,generation] { if (generation == pasteGeneration) paste(text); }); return true;
    }
private slots:
    void shortcut(const QString &name, const QString &id, qlonglong) {
        if (name != component) return;
        if (id == "toggle") Toggle(); else if (id == "cancel") Cancel();
    }
    void portalResponse(uint code, const QVariantMap &results, const QDBusMessage &message) {
        if (message.path() != requestPath) return;
        QDBusConnection::sessionBus().disconnect(portalService, requestPath,
            "org.freedesktop.portal.Request", "Response", this,
            SLOT(portalResponse(uint,QVariantMap,QDBusMessage)));
        requestPath.clear();
        if (code != 0) { setupFailed(QStringLiteral("مجوز تأیید نشد؛ می‌توانید دوباره فعال کنید.")); return; }
        if (phase == 1) {
            sessionPath = results.value("session_handle").toString();
            if (sessionPath.isEmpty()) { setupFailed("Portal returned no session"); return; }
            QVariantMap options{{"types", uint(1)}, {"persist_mode", uint(2)}};
            const auto restore = settings.value("restoreToken").toString();
            if (!restore.isEmpty()) options["restore_token"] = restore;
            request("SelectDevices", {QVariant::fromValue(QDBusObjectPath(sessionPath))}, options, 2);
        } else if (phase == 2) {
            request("Start", {QVariant::fromValue(QDBusObjectPath(sessionPath)), QString()}, {}, 3);
        } else if (phase == 3) {
            if (!(results.value("devices").toUInt() & 1)) { setupFailed("Keyboard permission missing"); return; }
            keyboardReady = true; setupBusy = false;
            if (results.contains("restore_token")) settings.setValue("restoreToken", results["restore_token"]);
            QDBusConnection::sessionBus().connect(portalService, sessionPath,
                "org.freedesktop.portal.Session", "Closed", this, SLOT(sessionClosed(QVariantMap)));
            report(QStringLiteral("آماده؛ پنجره را ببندید و در کادر مقصد Ctrl+Alt+W بزنید."));
        }
    }
    void sessionClosed(const QVariantMap &) {
        sessionPath.clear(); keyboardReady = false; setupBusy = false; Cancel();
        report(QStringLiteral("مجوز صفحه‌کلید پایان یافت؛ دوباره فعال کنید."));
    }
    void readWorker() {
        workerBuffer += worker.readAllStandardOutput();
        while (workerBuffer.contains('\n')) {
            const auto line = workerBuffer.left(workerBuffer.indexOf('\n'));
            workerBuffer.remove(0, line.size()+1);
            QJsonParseError error;
            const auto object = QJsonDocument::fromJson(line, &error).object();
            if (error.error != QJsonParseError::NoError || !busy) continue;
            if (object.contains("status")) { report(object["status"].toString()); continue; }
            busy = false; workerTimeout.stop(); cleanup();
            backend = object.toVariantMap();
            worker.closeWriteChannel();
            if (object.contains("error")) { report(object["error"].toString()); continue; }
            const auto text = object["text"].toString().trimmed();
            if (text.isEmpty()) { report(QStringLiteral("گفتاری تشخیص داده نشد؛ آماده.")); continue; }
            lastText = text; preview->setPlainText(text);
            rawText = object.value("originalText").toString(text);
            rawPreview->setPlainText(rawText);
            QStringList changes;
            for (const auto &entry : object.value("corrections").toArray()) {
                const auto change = entry.toObject();
                changes << change.value("from").toString() + " → " + change.value("to").toString();
            }
            correctionSummary->setText(changes.isEmpty() ? QStringLiteral("بدون اصلاح خودکار")
                : QStringLiteral("اصلاحات: ") + changes.join(QStringLiteral("، ")));
            if (object.contains("spellingWarning")) correctionSummary->setText(
                QStringLiteral("اصلاح واژه‌ها اجرا نشد؛ متن خام حفظ شد: ") + object.value("spellingWarning").toString());
            paste(text);
        }
    }
protected:
    void closeEvent(QCloseEvent *event) override {
        if (QSystemTrayIcon::isSystemTrayAvailable()) { hide(); event->ignore(); }
        else QWidget::closeEvent(event);
    }
private:
    QSettings settings;
    QLabel *status = nullptr;
    QPlainTextEdit *preview = nullptr, *rawPreview = nullptr;
    QLabel *correctionSummary = nullptr;
    QSystemTrayIcon *tray = nullptr;
    QProcess recorder, worker;
    QTimer maxRecording, workerTimeout;
    std::unique_ptr<QTemporaryFile> audio;
    QString rawPath, sessionPath, requestPath, lastText, rawText;
    QByteArray workerBuffer, diagnostics;
    QVariantMap backend;
    bool recording = false, busy = false, sendAfterStop = false;
    bool keyboardReady = false, setupBusy = false, terminalMode = false, shortcutsReady = false;
    int phase = 0;
    quint64 pasteGeneration = 0;
    void report(const QString &message) { status->setText(message); tray->setToolTip(message); qInfo().noquote() << message; }
    void cleanup() { audio.reset(); rawPath.clear(); }
    static QString token() { return "v" + QUuid::createUuid().toString(QUuid::Id128); }
    static QStringList actionId(const QString &id) {
        return {component, id, QStringLiteral("ورودی صوتی"), id == "toggle" ? QStringLiteral("شروع / پایان ضبط") : QStringLiteral("لغو")};
    }
    bool registerShortcuts() {
        qDBusRegisterMetaType<QList<int>>();
        QDBusInterface accel("org.kde.kglobalaccel", "/kglobalaccel", "org.kde.KGlobalAccel");
        if (!accel.isValid()) return false;
        for (const auto &id : {QString("toggle"), QString("cancel")}) {
            const auto action = actionId(id);
            const int key = int(Qt::CTRL | Qt::ALT) | int(id == "toggle" ? Qt::Key_W : Qt::Key_Escape);
            QDBusReply<bool> available = accel.call("isGlobalShortcutAvailable", key, component);
            if (!available.isValid()) return false;
            if (!available.value()) {
                QDBusReply<QStringList> owner = accel.call("action", key);
                if (owner.isValid() && owner.value().value(0) == component && owner.value().value(1) == id) {
                    // Reconnect to the shortcut retained across app restarts.
                } else if (id == "toggle" && owner.isValid() && owner.value().value(0) == "whisper-dictation.desktop"
                    && owner.value().value(1) == "_launch") {
                    const auto migrated = accel.call("setForeignShortcut", owner.value(), QVariant::fromValue(QList<int>{}));
                    if (migrated.type() == QDBusMessage::ErrorMessage) return false;
                    settings.setValue("migratedWhisperShortcut", key);
                    qInfo() << "Migrated previous Whisper shortcut";
                } else { qWarning() << "Shortcut occupied:" << id << owner.value(); return false; }
            }
            auto registered = accel.call("doRegister", action);
            if (registered.type() == QDBusMessage::ErrorMessage) return false;
            QDBusReply<QList<int>> assigned = accel.call("setShortcut", action, QVariant::fromValue(QList<int>{key}), uint(6)); // SetPresent | NoAutoloading
            if (!assigned.isValid() || !assigned.value().contains(key)) { qWarning() << assigned.error(); return false; }
        }
        QDBusReply<QDBusObjectPath> path = accel.call("getComponent", component);
        if (!path.isValid()) return false;
        return QDBusConnection::sessionBus().connect("org.kde.kglobalaccel", path.value().path(),
            "org.kde.kglobalaccel.Component", "globalShortcutPressed", this, SLOT(shortcut(QString,QString,qlonglong)));
    }
    void request(const QString &method, QVariantList args, QVariantMap options, int nextPhase) {
        phase = nextPhase;
        const auto handleToken = token(); options["handle_token"] = handleToken;
        QString sender = QDBusConnection::sessionBus().baseService().mid(1); sender.replace('.', '_');
        requestPath = "/org/freedesktop/portal/desktop/request/" + sender + "/" + handleToken;
        QDBusConnection::sessionBus().connect(portalService, requestPath,
            "org.freedesktop.portal.Request", "Response", this, SLOT(portalResponse(uint,QVariantMap,QDBusMessage)));
        args.append(options);
        auto message = QDBusMessage::createMethodCall(portalService, portalPath, portalInterface, method);
        message.setArguments(args);
        auto *watcher = new QDBusPendingCallWatcher(QDBusConnection::sessionBus().asyncCall(message), this);
        connect(watcher, &QDBusPendingCallWatcher::finished, this, [this,watcher](QDBusPendingCallWatcher *) {
            QDBusPendingReply<QDBusObjectPath> reply = *watcher;
            if (reply.isError()) setupFailed(reply.error().message());
            watcher->deleteLater();
        });
    }
    void closeSession() {
        if (!sessionPath.isEmpty()) {
            QDBusInterface session(portalService, sessionPath, "org.freedesktop.portal.Session");
            session.call(QDBus::NoBlock, "Close"); sessionPath.clear();
        }
        keyboardReady = false;
    }
    void setupFailed(const QString &error) {
        if (!requestPath.isEmpty()) QDBusConnection::sessionBus().disconnect(portalService, requestPath,
            "org.freedesktop.portal.Request", "Response", this, SLOT(portalResponse(uint,QVariantMap,QDBusMessage)));
        requestPath.clear(); setupBusy = false; closeSession(); report(error);
    }
    void editDictionary() {
        const auto path = QDir(QCoreApplication::applicationDirPath()).absoluteFilePath("../personal_dictionary.json");
        QFile input(path);
        QJsonObject data;
        if (input.open(QIODevice::ReadOnly)) {
            QJsonParseError error;
            const auto document = QJsonDocument::fromJson(input.readAll(), &error);
            if (error.error != QJsonParseError::NoError || !document.isObject()) {
                QMessageBox::warning(this, QStringLiteral("دیکشنری"), QStringLiteral("فایل دیکشنری معتبر نیست؛ برای حفظ محتوا بازنویسی نشد."));
                return;
            }
            data = document.object(); input.close();
        }
        QDialog dialog(this);
        dialog.setWindowTitle(QStringLiteral("دیکشنری شخصی")); dialog.resize(540, 480);
        auto *layout = new QVBoxLayout(&dialog);
        layout->addWidget(new QLabel(QStringLiteral("اسم‌ها و اصطلاحات محافظت‌شده؛ هر واژه در یک خط")));
        auto *words = new QPlainTextEdit;
        QStringList protectedWords;
        for (const auto &word : data.value("words").toArray()) protectedWords << word.toString();
        words->setPlainText(protectedWords.join('\n')); layout->addWidget(words);
        layout->addWidget(new QLabel(QStringLiteral("اصلاحات دلخواه؛ هر خط: غلط=درست (سمت چپ یک واژه)")));
        auto *rules = new QPlainTextEdit;
        QStringList ruleLines;
        const auto mapping = data.value("replacements").toObject();
        for (auto it = mapping.begin(); it != mapping.end(); ++it) ruleLines << it.key() + "=" + it.value().toString();
        rules->setPlainText(ruleLines.join('\n')); layout->addWidget(rules);
        auto *buttons = new QDialogButtonBox(QDialogButtonBox::Save | QDialogButtonBox::Cancel);
        layout->addWidget(buttons);
        connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
        connect(buttons, &QDialogButtonBox::accepted, &dialog, [&] {
            QJsonArray personal;
            for (const auto &word : words->toPlainText().split(QRegularExpression("\\s+"), Qt::SkipEmptyParts)) personal.append(word);
            QJsonObject replacements;
            for (const auto &line : rules->toPlainText().split('\n', Qt::SkipEmptyParts)) {
                if (line.trimmed().isEmpty()) continue;
                const auto separator = line.indexOf('=');
                const auto key = line.left(separator).trimmed();
                const auto value = line.mid(separator+1).trimmed();
                if (separator < 1 || key.contains(QRegularExpression("\\s")) || value.isEmpty()) {
                    QMessageBox::warning(&dialog, QStringLiteral("اصلاح"), QStringLiteral("هر خط باید غلط=درست باشد و سمت چپ فقط یک واژه باشد.")); return;
                }
                replacements.insert(key, value);
            }
            data["words"] = personal; data["replacements"] = replacements;
            QSaveFile output(path);
            if (!output.open(QIODevice::WriteOnly) || output.write(QJsonDocument(data).toJson()) < 0 || !output.commit()) {
                QMessageBox::warning(&dialog, QStringLiteral("دیکشنری"), QStringLiteral("ذخیرهٔ فایل ناموفق بود.")); return;
            }
            dialog.accept();
        });
        dialog.exec();
    }
    void transcribe() {
        workerTimeout.start(120000);
        if (worker.state() != QProcess::NotRunning) { worker.kill(); worker.waitForFinished(2000); }
        if (worker.state() == QProcess::NotRunning) {
            workerBuffer.clear(); diagnostics.clear();
            const auto python = QDir::homePath() + "/.local/share/whisper/venv/bin/python";
            QProcess paths;
            paths.start(python, {"-c", "import site;print(site.getsitepackages()[0])"});
            if (!paths.waitForFinished(5000) || paths.exitCode() != 0) {
                busy = false; workerTimeout.stop(); cleanup(); report(QStringLiteral("محیط Whisper قابل اجرا نیست.")); return;
            }
            const auto packages = QString::fromUtf8(paths.readAllStandardOutput()).trimmed();
            auto environment = QProcessEnvironment::systemEnvironment();
            environment.insert("LD_LIBRARY_PATH", packages + "/nvidia/cublas/lib:" + packages + "/nvidia/cudnn/lib:" + environment.value("LD_LIBRARY_PATH"));
            environment.insert("HF_HUB_OFFLINE", "1");
            worker.setProcessEnvironment(environment);
            const bool useFastConformer = settings.value("fastconformer", true).toBool();
            const auto root = QDir(QCoreApplication::applicationDirPath()).absoluteFilePath("..");
            if (useFastConformer) {
                QDir nvidia(root + "/fastconformer-venv/lib/python3.14/site-packages/nvidia");
                QStringList libraries;
                for (const auto &folder : nvidia.entryList(QDir::Dirs | QDir::NoDotAndDotDot))
                    libraries << nvidia.absoluteFilePath(folder + "/lib");
                environment.insert("LD_LIBRARY_PATH", libraries.join(':') + ":" + environment.value("LD_LIBRARY_PATH"));
                worker.setProcessEnvironment(environment);
            }
            const auto workerPython = useFastConformer ? root + "/fastconformer-venv/bin/python" : python;
            const auto workerScript = useFastConformer ? "/fastconformer_worker.py" : "/worker.py";
            worker.start(workerPython, {QCoreApplication::applicationDirPath() + workerScript});
            if (!worker.waitForStarted(3000)) return;
        }
        QJsonObject request{{"path", rawPath}, {"language", "fa"}, {"correctSpelling", settings.value("correctSpelling", true).toBool()}};
        worker.write(QJsonDocument(request).toJson(QJsonDocument::Compact) + '\n');
    }
    bool setClipboard(const QString &text) {
        QDBusInterface klipper("org.kde.klipper", "/klipper", "org.kde.klipper.klipper");
        if (klipper.isValid()) {
            const auto result = klipper.call("setClipboardContents", text);
            if (result.type() != QDBusMessage::ErrorMessage) return true;
        }
        QApplication::clipboard()->setText(text);
        return QApplication::clipboard()->text() == text;
    }
    bool key(int code, uint state) {
        QDBusInterface input(portalService, portalPath, portalInterface);
        auto reply = input.call("NotifyKeyboardKeycode", QVariant::fromValue(QDBusObjectPath(sessionPath)), QVariantMap{}, code, state);
        if (reply.type() == QDBusMessage::ErrorMessage) { qWarning() << reply.errorMessage(); return false; }
        return true;
    }
    void paste(const QString &text) {
        if (!keyboardReady) { report(QStringLiteral("مجوز صفحه‌کلید فعال نیست؛ متن را از تنظیمات کپی کنید.")); return; }
        if (!setClipboard(text)) { report(QStringLiteral("کپی متن ناموفق بود.")); return; }
        // Delay until the physical shortcut modifiers have been released.
        const auto generation = pasteGeneration;
        QTimer::singleShot(350, this, [this,generation] {
            if (!keyboardReady || generation != pasteGeneration) return;
            bool ok = key(29, 1); // Linux evdev left Ctrl
            if (terminalMode) ok = key(42, 1) && ok;
            ok = key(47, 1) && ok; // V
            ok = key(47, 0) && ok;
            if (terminalMode) ok = key(42, 0) && ok;
            ok = key(29, 0) && ok;
            report(ok ? QStringLiteral("متن برای کادر فعال فرستاده شد؛ آماده.")
                      : QStringLiteral("ارسال کلید ناموفق بود؛ متن را از تنظیمات کپی کنید."));
        });
    }
};

int main(int argc, char **argv) {
    QApplication app(argc, argv);
    app.setOrganizationName("LocalVoiceInput"); app.setApplicationName("VoiceInput");
    app.setDesktopFileName("local.voiceinput");
    if (app.arguments().contains("--test-target")) {
        QWidget window; auto *layout = new QVBoxLayout(&window);
        layout->addWidget(new QLabel(QStringLiteral("کادر آزمایش درج متن")));
        auto *edit = new QLineEdit; layout->addWidget(edit);
        QObject::connect(edit, &QLineEdit::textChanged, &app, [](const QString &text) { qInfo().noquote() << "INSERTED:" << text; });
        window.setWindowTitle("Voice Input Paste Test");
        window.resize(480, 120); window.show(); window.raise(); window.activateWindow(); edit->setFocus();
        if (app.arguments().contains("--auto-exit")) QTimer::singleShot(30000, &app, &QCoreApplication::quit);
        return app.exec();
    }
    auto bus = QDBusConnection::sessionBus();
    if (!bus.isConnected()) { qCritical() << "Desktop session D-Bus unavailable"; return 1; }
    if (!bus.registerService("local.voiceinput.Controller")) {
        QDBusInterface existing("local.voiceinput.Controller", "/VoiceInput", "local.voiceinput.Controller");
        existing.call(app.arguments().contains("--toggle") ? "Toggle" : "Show"); return 0;
    }
    app.setQuitOnLastWindowClosed(false);
    VoiceInput window;
    bus.registerObject("/VoiceInput", &window, QDBusConnection::ExportScriptableSlots);
    if (!app.arguments().contains("--background")) window.show();
    if (app.arguments().contains("--setup")) QTimer::singleShot(500, &window, &VoiceInput::Setup);
    return app.exec();
}
#include "main.moc"
