import 'package:flutter/material.dart';
import 'package:flutter_hbb/common.dart';
import 'package:flutter_hbb/consts.dart';
import 'package:flutter_hbb/models/platform_model.dart';
import 'package:url_launcher/url_launcher.dart';

const String _brandSite = '@@SITE@@';
const String _brandTicket = '@@TICKET@@';
const String _brandCompanyFa = '@@COMPANY_FA@@';
const String _brandCompanyEn = '@@COMPANY_EN@@';
const String _brandDescFa = '@@DESC_FA@@';
const String _brandDescEn = '@@DESC_EN@@';
const String _brandCopyright = '@@COPYRIGHT@@';
const Color _brandOrange = Color(0xFFF39F1F);
const Color _brandGrey = Color(0xFF7A7D92);

/// Branded footer for the customer build: language switch, ticket and site
/// links and an About dialog.
class BrandFooter extends StatefulWidget {
  const BrandFooter({Key? key}) : super(key: key);

  @override
  State<BrandFooter> createState() => _BrandFooterState();
}

class _BrandFooterState extends State<BrandFooter> {
  late bool fa;

  @override
  void initState() {
    super.initState();
    fa = bind.mainGetLocalOption(key: kCommConfKeyLang) != 'en';
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
              ],
            ),
          ],
        ),
      ),
    );
  }
}
