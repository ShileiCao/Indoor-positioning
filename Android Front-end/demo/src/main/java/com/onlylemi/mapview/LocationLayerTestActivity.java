package com.onlylemi.mapview;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.PointF;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.Toast;

import com.onlylemi.mapview.library.MapView;
import com.onlylemi.mapview.library.MapViewListener;
import com.onlylemi.mapview.library.layer.LocationLayer;

import java.io.IOException;
import java.util.Timer;
import java.util.TimerTask;

public class LocationLayerTestActivity extends AppCompatActivity implements SensorEventListener {

    private MapView mapView;

    private LocationLayer locationLayer;

    private boolean openSensor = false;

    private SensorManager sensorManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_location_layer_test);

        mapView = (MapView) findViewById(R.id.mapview);
        Bitmap bitmap = null;
        try {
            bitmap = BitmapFactory.decodeStream(getAssets().open("map.png"));
        } catch (IOException e) {
            e.printStackTrace();
        }
        mapView.loadMap(bitmap);
        mapView.setMapViewListener(new MapViewListener() {
            @Override
            public void onMapLoadSuccess() {
                final PointF startPoint = new PointF(0, 0);
                locationLayer = new LocationLayer(mapView, startPoint);
                locationLayer.setOpenCompass(false);
                /*locationLayer.setCompassIndicatorCircleRotateDegree(60);
                locationLayer.setCompassIndicatorArrowRotateDegree(-30);*/
                mapView.addLayer(locationLayer);
                mapView.refresh();

                // 创建计时器，每0.1秒更新一次位置
                Timer timer = new Timer();
                timer.schedule(new TimerTask() {
                    int secondsElapsed = 0;

                    @Override
                    public void run() {
                        // 每秒增加100的变化
                        //int incrementPerSecond = 100;

                        // 更新PointF的值
                        PointF point = locationLayer.getCurrentPosition();
                        float newX = (float) (point.x * 0.072); //startPoint.x + (incrementPerSecond * secondsElapsed);
                        float newY = (float) (0.072 * (113800-point.y)); //startPoint.y + (incrementPerSecond * secondsElapsed);
                        PointF newPoint = new PointF(newX, newY);

                        // 在UI线程更新位置
                        runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                locationLayer.setCurrentPosition(newPoint);
                                mapView.refresh();
                            }
                        });

                        secondsElapsed++;

                        // 99999秒内持续更新
                        if (secondsElapsed > 99999) {
                            timer.cancel();
                            timer.purge();
                        }
                    }
                }, 0, 200); // 0表示立即开始计时，每300ms触发一次
            }

            @Override
            public void onMapLoadFail() {

            }

        });


        sensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.menu_location_layer_test, menu);
        return super.onCreateOptionsMenu(menu);
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (mapView.isMapLoadFinish()) {
            switch (item.getItemId()) {
                case R.id.location_layer_set_mode:
                    if (locationLayer.isOpenCompass()) {
                        item.setTitle("Open Compass");
                    } else {
                        item.setTitle("Close Compass");
                    }
                    locationLayer.setOpenCompass(!locationLayer.isOpenCompass());
                    mapView.refresh();
                    break;
                case R.id.location_layer_set_compass_circle_rotate:
                    float rotate = 90;
                    locationLayer.setCompassIndicatorCircleRotateDegree(rotate);
                    mapView.refresh();
                    Toast.makeText(this, "circle rotate: " + rotate, Toast.LENGTH_SHORT).show();
                    break;
                case R.id.location_layer_set_compass_arrow_rotate:
                    rotate = 30;
                    locationLayer.setCompassIndicatorArrowRotateDegree(rotate);
                    mapView.refresh();
                    Toast.makeText(this, "arrow rotate: " + rotate, Toast.LENGTH_SHORT).show();
                    break;
                case R.id.location_layer_set_auto_sensor:
                    if (openSensor) {
                        item.setTitle("Open Sensor");
                        sensorManager.unregisterListener(this);
                    } else {
                        item.setTitle("Close Sensor");
                        sensorManager.registerListener(this, sensorManager.getDefaultSensor
                                (Sensor.TYPE_ORIENTATION), SensorManager.SENSOR_DELAY_NORMAL);
                    }
                    openSensor = !openSensor;
                    break;
                default:
                    break;
            }
        }
        return super.onOptionsItemSelected(item);
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (mapView.isMapLoadFinish() && openSensor) {
            float mapDegree = 0; // the rotate between reality map to northern
            float degree = 0;
            if (event.sensor.getType() == Sensor.TYPE_ORIENTATION) {
                degree = event.values[0];
            }

            locationLayer.setCompassIndicatorCircleRotateDegree(-degree);
            locationLayer.setCompassIndicatorArrowRotateDegree(mapDegree + mapView
                    .getCurrentRotateDegrees() + degree);
            mapView.refresh();
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {

    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        sensorManager.unregisterListener(this);
    }
}
