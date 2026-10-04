(function(root){
  'use strict';
  function analyze(rows,settings){
    const qty=Number(settings.quantity), maxDays=Number(settings.maxDays), minWarranty=Number(settings.minWarranty);
    const weights=settings.weights.map(Number);
    if(!Number.isInteger(qty)||qty<1||qty>1000000) throw Error('Quantity must be a whole number between 1 and 1,000,000.');
    if(!Number.isFinite(maxDays)||maxDays<0||!Number.isFinite(minWarranty)||minWarranty<0) throw Error('Delivery and warranty requirements must be zero or positive.');
    if(weights.some(w=>!Number.isFinite(w)||w<0)||weights.reduce((a,b)=>a+b,0)===0) throw Error('Set at least one scoring weight above zero.');
    if(!rows.length) throw Error('Add at least one supplier quotation.');
    const names=new Set();
    const result=rows.map((r,i)=>{
      const name=String(r.supplier||'').trim();
      if(!name) throw Error(`Quotation ${i+1}: enter a supplier name.`);
      if(names.has(name.toLowerCase())) throw Error(`Supplier names must be unique: ${name}.`);
      names.add(name.toLowerCase());
      const v={};
      for(const key of ['unitPrice','discount','tax','freight','days','warranty']){
        if(String(r[key]??'').trim()==='') throw Error(`${name}: ${key} is required.`);
        v[key]=Number(r[key]);
        if(!Number.isFinite(v[key])||v[key]<0||v[key]>1e12) throw Error(`${name}: ${key} must be a valid positive number or zero.`);
      }
      if(v.unitPrice<=0) throw Error(`${name}: unit price must be greater than zero.`);
      if(v.discount>100||v.tax>100) throw Error(`${name}: tax and discount must be between 0 and 100%.`);
      const gross=qty*v.unitPrice,discountAmount=gross*v.discount/100,net=gross-discountAmount,taxAmount=net*v.tax/100;
      const total=net+taxAmount+v.freight;
      const reasons=[];
      if(maxDays>0&&v.days>maxDays) reasons.push('Delivery exceeds requirement');
      if(v.warranty<minWarranty) reasons.push('Warranty below requirement');
      return {supplier:name,...v,gross,discountAmount,net,taxAmount,total,eligible:reasons.length===0,reasons,score:null};
    });
    const eligible=result.filter(r=>r.eligible),sum=weights.reduce((a,b)=>a+b,0);
    if(eligible.length){
      const costs=eligible.map(r=>r.total),days=eligible.map(r=>r.days),warranties=eligible.map(r=>r.warranty);
      const scale=(value,values,lower)=>{const lo=Math.min(...values),hi=Math.max(...values);return hi===lo?1:lower?(hi-value)/(hi-lo):(value-lo)/(hi-lo);};
      eligible.forEach(r=>r.score=100*(weights[0]*scale(r.total,costs,true)+weights[1]*scale(r.days,days,true)+weights[2]*scale(r.warranty,warranties,false))/sum);
    }
    result.sort((a,b)=>Number(b.eligible)-Number(a.eligible)||(b.score??0)-(a.score??0)||a.total-b.total||a.days-b.days||a.supplier.localeCompare(b.supplier));
    const leaders=eligible.length?result.filter(r=>r.eligible&&Math.abs(r.score-result[0].score)<1e-8):[];
    return {rows:result,eligibleCount:eligible.length,leaders,weights:weights.map(w=>w/sum*100)};
  }
  const headers=['supplier','unitPrice','discount','tax','freight','days','warranty'];
  function parseCSV(text){
    text=text.replace(/^\uFEFF/,'');
    let rows=[],row=[],cell='',quoted=false;
    for(let i=0;i<text.length;i++){
      const c=text[i];
      if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++;}else if(quoted){quoted=false;}else if(cell===''){quoted=true;}else throw Error('Invalid quote in CSV.');}
      else if(c===','&&!quoted){row.push(cell);cell='';}
      else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(v=>v.trim()))rows.push(row);row=[];cell='';}
      else cell+=c;
    }
    if(quoted) throw Error('CSV contains an unclosed quoted field.');
    row.push(cell);if(row.some(v=>v.trim()))rows.push(row);
    if(!rows.length||rows[0].map(v=>v.trim()).join(',')!==headers.join(',')) throw Error('CSV headers do not match. Download the template and keep its headers.');
    if(rows.length<2||rows.length>51) throw Error('Import between 1 and 50 suppliers.');
    return rows.slice(1).map((r,i)=>{if(r.length!==headers.length)throw Error(`CSV row ${i+2}: expected 7 columns.`);return Object.fromEntries(headers.map((h,j)=>[h,r[j].trim()]));});
  }
  function csv(rows,columns){return columns.join(',')+'\r\n'+rows.map(r=>columns.map(k=>{let value=String(r[k]??'');if(/^[=+@\-\t\r]/.test(value))value="'"+value;return '"'+value.replace(/"/g,'""')+'"';}).join(',')).join('\r\n');}
  const api={analyze,parseCSV,csv,headers};
  if(typeof module!=='undefined')module.exports=api;else root.QuotationModel=api;
})(typeof globalThis!=='undefined'?globalThis:this);
