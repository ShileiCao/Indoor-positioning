package com.onlylemi.mapview;

import android.content.Context;
import android.net.wifi.ScanResult;
import android.net.wifi.WifiManager;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Environment;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.RequestBody;
import okhttp3.MediaType;
import okhttp3.Callback;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Timer;
import java.util.TimerTask;

public class DataReader implements SensorEventListener {

    private Context context;
    private SensorManager sensorManager;
    private WifiManager wifiManager;
    private static final String TAG = "111111";
    private static final String API_URL = "http://172.20.10.5:5000/receive";
    private JSONObject lastestMagnetometerData;
    private JSONObject lastestOrientationData;

    private OkHttpClient client = new OkHttpClient();
    private MediaType mediaType = MediaType.parse("application/json; charset=utf-8");

    public DataReader(Context context) {
        this.context = context;
        sensorManager = (SensorManager) context.getSystemService(Context.SENSOR_SERVICE);
        wifiManager = (WifiManager) context.getApplicationContext().getSystemService(Context.WIFI_SERVICE);
    }

    public void startReading() {
        // Check permissions
        /*
        if (ActivityCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            // Handle permission not granted
            return;
        }
        */
        MediaType mediaType = MediaType.parse("application/json; charset=utf-8");

        // Schedule timer to read data every second
        Timer timer = new Timer();
        timer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                readData();
            }
        }, 0, 1000);
    }

    private void readData() {
        JSONObject dataObject = new JSONObject();
        try {
            // Read WiFi information
            JSONArray wifiArray = new JSONArray();
            wifiManager.startScan();
            List<ScanResult> scanResults = wifiManager.getScanResults();
            for (ScanResult scanResult : scanResults) {
                JSONObject wifiObject = new JSONObject();
                wifiObject.put("SSID", scanResult.SSID);
                wifiObject.put("BSSID", scanResult.BSSID);
                wifiObject.put("SignalStrength", scanResult.level);
                wifiArray.put(wifiObject);
            }
            dataObject.put("WiFi", wifiArray);
            
            Sensor magnetometerSensor = sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD);
            sensorManager.registerListener(this, magnetometerSensor, SensorManager.SENSOR_DELAY_NORMAL);

            Sensor orientationSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ORIENTATION);
            sensorManager.registerListener(this, orientationSensor, SensorManager.SENSOR_DELAY_NORMAL);

            // Save data as JSON file
            if (lastestMagnetometerData != null && lastestOrientationData != null)  {
                dataObject.put("mag", lastestMagnetometerData);
                dataObject.put("ori", lastestOrientationData);
                RequestBody requestBody = RequestBody.create(mediaType, dataObject.toString());
                String responseContent = dataObject.toString();
                Request request = new Request.Builder()
                        .url(API_URL)
                        .post(requestBody)
                        .build();
                client.newCall(request).enqueue(new Callback() {
                    @Override
                    public void onFailure(okhttp3.Call call, IOException e) {
                        e.printStackTrace();
                        Log.e(TAG, "fail");
                    }
                    @Override
                    public void onResponse(okhttp3.Call call, Response response) throws IOException {
                        if (response.isSuccessful()) {
                            String responseContent = response.body().string();
                            Log.d(TAG, "响应数据：" + responseContent);
                        } else {
                            Log.e(TAG, "请求失败");
                        }
                    }
                });
            }

        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        // Read magnetometer data
        if (event.sensor.getType() == Sensor.TYPE_MAGNETIC_FIELD) {
            float x = event.values[0];
            float y = event.values[1];
            float z = event.values[2];

            try {
                JSONObject dataObject = new JSONObject();
                dataObject.put("x", x);
                dataObject.put("y", y);
                dataObject.put("z", z);

                lastestMagnetometerData = dataObject;
            } catch (JSONException e) {
                e.printStackTrace();
            }
        }

        // Read orientation data
        if (event.sensor.getType() == Sensor.TYPE_ORIENTATION) {
            float azimuth = event.values[0];
            float pitch = event.values[1];
            float roll = event.values[2];

            try {
                JSONObject dataObject = new JSONObject();
                dataObject.put("azimuth", azimuth);
                dataObject.put("pitch", pitch);
                dataObject.put("roll", roll);

                lastestOrientationData = dataObject;
            } catch (JSONException e) {
                e.printStackTrace();
            }
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
        // Do nothing
    }

    private void saveData(JSONObject data, boolean isMagnetometer) {
        try {
            // Create file name using current time
            String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
            String fileName = timeStamp + (isMagnetometer ? "_magnetometer.json" : "_wifi.json");
            // Specify the folder path
            File folder = new File(Environment.getExternalStorageDirectory(), "wifiData");
            if (!folder.exists()) {
                folder.mkdirs(); // Create the folder if it doesn't exist
            }

            // Create JSON file
            File file = new File(folder, fileName);
            FileWriter writer = new FileWriter(file);
            writer.write(data.toString());
            writer.flush();
            writer.close();

            // Log file path for verification
            Log.d("DataReader", "Data saved: " + file.getAbsolutePath());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
