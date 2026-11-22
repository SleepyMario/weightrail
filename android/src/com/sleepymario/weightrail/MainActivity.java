package com.sleepymario.weightrail;

import android.app.Activity;
import android.os.Bundle;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.text.InputType;
import android.view.View;
import android.widget.*;
import java.time.LocalDate;

/** Minimal offline Android companion. Its private database is separate from desktop data. */
public class MainActivity extends Activity {
    private SQLiteDatabase db;
    private EditText date, weight, systolic, diastolic, pulse;
    private TextView status, history;
    private LinearLayout column;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        ScrollView scroll = new ScrollView(this);
        column = new LinearLayout(this); column.setOrientation(LinearLayout.VERTICAL);
        int pad=(int)(20*getResources().getDisplayMetrics().density);
        column.setPadding(pad,pad,pad,pad); scroll.setFillViewport(true); scroll.addView(column); setContentView(scroll);
        text("Weightrail",28); text("0.5.0 · Android preview",16);
        text("Your measurements, stored on this device. Desktop records are not imported or changed.",16);
        date=field("Date (YYYY-MM-DD)",false); date.setText(LocalDate.now().toString());
        weight=field("Weight (kg)",true); systolic=field("Systolic (mmHg)",true);
        diastolic=field("Diastolic (mmHg)",true); pulse=field("Resting heart rate (bpm)",true);
        Button save=new Button(this); save.setText("Save measurements"); column.addView(save);
        status=text("Enter any measurement. Saving again updates only the fields you enter for that date.",15);
        text("Recent measurements",22); history=text("",16);
        db=openOrCreateDatabase("weightrail.sqlite",MODE_PRIVATE,null);
        db.execSQL("CREATE TABLE IF NOT EXISTS measurements (day TEXT PRIMARY KEY, weight REAL, systolic INTEGER, diastolic INTEGER, pulse INTEGER)");
        save.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { save(); } }); refresh();
    }
    private TextView text(String value,int size) {
        TextView v=new TextView(this); v.setText(value);v.setTextSize(size);v.setPadding(0,10,0,10);column.addView(v);return v;
    }
    private EditText field(String label,boolean numeric) {
        text(label,15);EditText v=new EditText(this);v.setHint(label);v.setSingleLine(true);
        v.setInputType(numeric ? InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL : InputType.TYPE_CLASS_TEXT);
        column.addView(v,new LinearLayout.LayoutParams(-1,-2));return v;
    }
    private String value(EditText v){return v.getText().toString().trim();}
    private void integer(ContentValues values,String name,EditText field) {
        if(value(field).isEmpty())return;
        int n=Integer.parseInt(value(field)); if(n<=0)throw new IllegalArgumentException("Measurements must be positive.");values.put(name,n);
    }
    private void save() {
        try {
            String day=LocalDate.parse(value(date)).toString();ContentValues values=new ContentValues();
            if(!value(weight).isEmpty()) { double w=Double.parseDouble(value(weight));if(!Double.isFinite(w)||w<=0)throw new IllegalArgumentException("Weight must be positive.");values.put("weight",w); }
            if(value(systolic).isEmpty()!=value(diastolic).isEmpty())throw new IllegalArgumentException("Enter both blood-pressure numbers.");
            integer(values,"systolic",systolic);integer(values,"diastolic",diastolic);integer(values,"pulse",pulse);
            if(values.size()==0)throw new IllegalArgumentException("Enter at least one measurement.");
            db.beginTransaction();try { if(db.update("measurements",values,"day=?",new String[]{day})==0) {values.put("day",day);db.insertOrThrow("measurements",null,values);}db.setTransactionSuccessful(); }finally {db.endTransaction();}
            status.setText("Saved for "+day+". Stored locally on this device.");refresh();
        } catch(Exception e) { status.setText("Could not save. Check the date and measurement fields. "+(e instanceof IllegalArgumentException?e.getMessage():"Your existing records are retained.")); }
    }
    private void refresh() {
        StringBuilder out=new StringBuilder();
        try(Cursor c=db.rawQuery("SELECT day,weight,systolic,diastolic,pulse FROM measurements ORDER BY day DESC LIMIT 30",null)) {
            while(c.moveToNext()) {
                out.append(c.getString(0));if(!c.isNull(1))out.append("\nWeight: ").append(c.getString(1)).append(" kg");
                if(!c.isNull(2))out.append("\nBlood pressure: ").append(c.getInt(2)).append('/').append(c.getInt(3)).append(" mmHg");
                if(!c.isNull(4))out.append("\nResting heart rate: ").append(c.getInt(4)).append(" bpm");out.append("\n\n");
            }
        }
        history.setText(out.length()==0?"No measurements yet.":out.toString());
    }
    @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}
}
