import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_hbb/common.dart';
import 'package:flutter_hbb/consts.dart';
import 'package:flutter_hbb/models/platform_model.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

const String brandVersion = '@@APP_VERSION@@';
const String _brandSite = '@@SITE@@';
const String _brandTicket = '@@TICKET@@';
const String _brandCompanyFa = '@@COMPANY_FA@@';
const String _brandCompanyEn = '@@COMPANY_EN@@';
const String _brandDescFa = '@@DESC_FA@@';
const String _brandDescEn = '@@DESC_EN@@';
const String _brandCopyright = '@@COPYRIGHT@@';
const String _brandDeveloper = '@@DEVELOPER@@';
const String _brandDevEmail = '@@DEV_EMAIL@@';
const String _brandUpdateUrl = '@@UPDATE_URL@@';
const Color _brandOrange = Color(0xFFF39F1F);
const Color _brandGrey = Color(0xFF7A7D92);
const Color _brandRed = Color(0xFFFF4D4D);

bool _isFa() => bind.mainGetLocalOption(key: kCommConfKeyLang) != 'en';

/// Slogan shown in the About page of the settings (replaces the original one).
class BrandSlogan extends StatelessWidget {
  const BrandSlogan({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final fa = _isFa();
    const base = TextStyle(fontWeight: FontWeight.w800, color: Colors.white);
    const red = TextStyle(fontWeight: FontWeight.w800, color: _brandRed);
    return Directionality(
      textDirection: fa ? TextDirection.rtl : TextDirection.ltr,
      child: Text.rich(
        TextSpan(
          style: base,
          children: fa
              ? const [
                  TextSpan(text: 'شما هم به داشتن یک '),
                  TextSpan(text: 'دستیار', style: red),
                  TextSpan(text: ' بیاندیشید'),
                ]
              : const [
                  TextSpan(text: 'Think about having a '),
                  TextSpan(text: 'Dastyar', style: red),
                  TextSpan(text: ' of your own'),
                ],
        ),
      ),
    );
  }
}

int _compareVersions(String a, String b) {
  final x = a.split('.').map((e) => int.tryParse(e.trim()) ?? 0).toList();
  final y = b.split('.').map((e) => int.tryParse(e.trim()) ?? 0).toList();
  for (var i = 0; i < 4; i++) {
    final p = i < x.length ? x[i] : 0;
    final q = i < y.length ? y[i] : 0;
    if (p != q) {
      return p < q ? -1 : 1;
    }
  }
  return 0;
}

bool _isWebUrl(String url) =>
    url.startsWith('https://') || url.startsWith('http://');

/// Branded footer for the customer build: language switch, ticket and site
/// links, About dialog and the version / forced update check.
class BrandFooter extends StatefulWidget {
  const BrandFooter({Key? key}) : super(key: key);

  @override
  State<BrandFooter> createState() => _BrandFooterState();
}

class _BrandFooterState extends State<BrandFooter> {
  late bool fa;
  String _newVersionUrl = '';

  @override
  void initState() {
    super.initState();
    fa = _isFa();
    _checkUpdate();
  }

  Future<void> _open(String url) async {
    try {
      await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
    } catch (_) {}
  }

  Future<void> _setLang(bool toFa) async {
    final key = toFa ? 'fa' : 'en';
    await bind.mainSetLocalOption(key: kCommConfKeyLang, value: key);
    if (!isWeb) reloadAllWindows();
    if (!isWeb) bind.mainChangeLanguage(lang: key);
    if (mounted) {
      setState(() {
        fa = toFa;
      });
    }
  }

  /// Reads a small JSON file from our own server:
  /// {"latest":"1.0.1","min":"1.0.0","url":"https://...",
  ///  "message_fa":"...","message_en":"..."}
  /// If the server cannot be reached the app simply keeps working.
  Future<void> _checkUpdate() async {
    if (_brandUpdateUrl.isEmpty) return;
    try {
      final id = await bind.mainGetMyId();
      final uri = Uri.parse(_brandUpdateUrl)
          .replace(queryParameters: {'v': brandVersion, 'id': id});
      final resp = await http.get(uri).timeout(const Duration(seconds: 8));
      if (resp.statusCode != 200) return;
      final data = jsonDecode(utf8.decode(resp.bodyBytes));
      if (data is! Map) return;
      final latest = (data['latest'] ?? '').toString();
      final minimum = (data['min'] ?? '').toString();
      final url = (data['url'] ?? '').toString();
      final msgFa = (data['message_fa'] ?? '').toString();
      final msgEn = (data['message_en'] ?? '').toString();
      final hasUrl = _isWebUrl(url);
      if (!mounted) return;
      if (minimum.isNotEmpty && _compareVersions(brandVersion, minimum) < 0) {
        _showForcedUpdate(hasUrl ? url : _brandSite, msgFa, msgEn);
        return;
      }
      if (latest.isNotEmpty &&
          hasUrl &&
          _compareVersions(brandVersion, latest) < 0) {
        setState(() {
          _newVersionUrl = url;
        });
      }
    } catch (_) {}
  }

  void _showForcedUpdate(String url, String msgFa, String msgEn) {
    final text = fa
        ? (msgFa.isNotEmpty
            ? msgFa
            : 'این نگارش برنامه دیگر پشتیبانی نمی‌شود. لطفاً نگارش جدید را دریافت کنید.')
        : (msgEn.isNotEmpty
            ? msgEn
            : 'This version is no longer supported. Please download the new version.');
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => WillPopScope(
        onWillPop: () async => false,
        child: Directionality(
          textDirection: fa ? TextDirection.rtl : TextDirection.ltr,
          child: AlertDialog(
            title: Text(fa ? 'به‌روزرسانی لازم است' : 'Update required',
                style: const TextStyle(fontSize: 16)),
            content: SizedBox(
              width: 300,
              child: Text(text, style: const TextStyle(fontSize: 13, height: 1.7)),
            ),
            actions: [
              TextButton(
                onPressed: () => exit(0),
                child: Text(fa ? 'خروج' : 'Exit'),
              ),
              ElevatedButton(
                onPressed: () => _open(url),
                child: Text(fa ? 'دریافت نگارش جدید' : 'Download update'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showAbout() {
    final company = fa ? _brandCompanyFa : _brandCompanyEn;
    final desc = fa ? _brandDescFa : _brandDescEn;
    showDialog<void>(
      context: context,
      builder: (ctx) => Directionality(
        textDirection: fa ? TextDirection.rtl : TextDirection.ltr,
        child: AlertDialog(
          title: Row(
            children: [
              Image.asset('assets/icon.png', width: 40, height: 40),
              const SizedBox(width: 10),
              Expanded(
                child: Text(company, style: const TextStyle(fontSize: 16)),
              ),
            ],
          ),
          content: SizedBox(
            width: 300,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(desc, style: const TextStyle(fontSize: 13, height: 1.7)),
                const SizedBox(height: 14),
                Text('${fa ? 'نگارش' : 'Version'}: $brandVersion',
                    style: const TextStyle(fontSize: 12)),
                if (_brandDeveloper.isNotEmpty)
                  Text('${fa ? 'توسعه‌دهنده' : 'Developer'}: $_brandDeveloper',
                      style: const TextStyle(fontSize: 12)),
                if (_brandDevEmail.isNotEmpty)
                  Text(_brandDevEmail, style: const TextStyle(fontSize: 12)),
                const SizedBox(height: 14),
                InkWell(
                  onTap: () => _open(_brandSite),
                  child: Text(_brandSite,
                      style: const TextStyle(
                          color: _brandOrange,
                          decoration: TextDecoration.underline)),
                ),
                const SizedBox(height: 6),
                InkWell(
                  onTap: () => _open(_brandTicket),
                  child: Text(_brandTicket,
                      style: const TextStyle(
                          color: _brandOrange,
                          decoration: TextDecoration.underline)),
                ),
                const SizedBox(height: 14),
                Text(_brandCopyright,
                    style: const TextStyle(fontSize: 10, color: _brandGrey)),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: Text(fa ? 'بستن' : 'Close'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _linkButton(IconData icon, String label, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 15, color: _brandOrange),
            const SizedBox(width: 4),
            Text(label, style: const TextStyle(fontSize: 12)),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: fa ? TextDirection.rtl : TextDirection.ltr,
      child: Container(
        margin: const EdgeInsets.fromLTRB(16, 8, 16, 8),
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          border: Border.all(color: _brandGrey.withOpacity(0.35)),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Text(
              fa ? _brandCompanyFa : _brandCompanyEn,
              style: const TextStyle(
                  fontSize: 12, fontWeight: FontWeight.bold, color: _brandGrey),
            ),
            const SizedBox(height: 4),
            Wrap(
              alignment: WrapAlignment.center,
              children: [
                _linkButton(Icons.support_agent,
                    fa ? 'تیکت پشتیبانی' : 'Support ticket',
                    () => _open(_brandTicket)),
                _linkButton(Icons.language, fa ? 'وب‌سایت' : 'Website',
                    () => _open(_brandSite)),
                _linkButton(Icons.info_outline, fa ? 'درباره' : 'About',
                    _showAbout),
                _linkButton(Icons.translate, fa ? 'English' : 'فارسی',
                    () => _setLang(!fa)),
                if (_newVersionUrl.isNotEmpty)
                  _linkButton(Icons.system_update,
                      fa ? 'نگارش جدید موجود است' : 'New version available',
                      () => _open(_newVersionUrl)),
              ],
            ),
            Text(
              '${fa ? 'نگارش' : 'Version'} $brandVersion',
              style: const TextStyle(fontSize: 10, color: _brandGrey),
            ),
          ],
        ),
      ),
    );
  }
}
