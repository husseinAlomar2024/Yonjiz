package com.yonjiz.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Build;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

/**
 * YONJIZ mobile shell.
 *
 * The UI is local HTML/CSS/JS in android_asset. Task data is a JSON file in the
 * app's private files directory. There is no HTTP server, no network permission
 * and no remote sync.
 */
public class MainActivity extends Activity {

    private WebView webView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().setStatusBarColor(Color.rgb(23, 75, 59));
        getWindow().setNavigationBarColor(Color.rgb(244, 241, 234));
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
            );
        }

        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(244, 241, 234));
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(false);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        webView.addJavascriptInterface(new StorageBridge(), "YonjizStore");
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !request.getUrl().toString().startsWith("file:///android_asset/");
            }
        });

        setContentView(webView);
        webView.loadUrl("file:///android_asset/index.html");
    }

    @Override
    public void onBackPressed() {
        if (webView == null) {
            super.onBackPressed();
            return;
        }
        webView.evaluateJavascript(
                "(window.mobileBack && window.mobileBack()) ? 'true' : 'false'",
                value -> {
                    if (!"true".equals(value)) {
                        finish();
                    }
                }
        );
    }

    /** Native file bridge. No network, no server. */
    public class StorageBridge {

        private File dataFile() {
            return new File(getFilesDir(), "yonjiz-mobile.json");
        }

        @JavascriptInterface
        public String load() {
            File file = dataFile();
            if (!file.exists()) {
                return "{}";
            }
            try (InputStream in = new FileInputStream(file)) {
                byte[] bytes = new byte[(int) file.length()];
                int read = in.read(bytes);
                if (read <= 0) {
                    return "{}";
                }
                return new String(bytes, 0, read, StandardCharsets.UTF_8);
            } catch (Exception exc) {
                return "{}";
            }
        }

        @JavascriptInterface
        public void save(String json) {
            try {
                File temp = new File(getFilesDir(), "yonjiz-mobile.json.tmp");
                try (OutputStream out = new FileOutputStream(temp)) {
                    out.write(json.getBytes(StandardCharsets.UTF_8));
                    out.flush();
                }
                File target = dataFile();
                if (target.exists() && !target.delete()) {
                    return;
                }
                temp.renameTo(target);
            } catch (Exception ignored) {
                // The UI keeps its in-memory copy; a failed disk write is non-fatal.
            }
        }

        @JavascriptInterface
        public String platform() {
            return "android";
        }
    }
}
