(function(root){
'use strict';
const headers=['itemCode','itemName','location','unit','bookQty','physicalQty','unitCost'];
function evaluate(items){
 if(!items.length)throw Error('Add at least one stock item.');
 const seen=new Set();
 const rows=items.map((r,i)=>{
  const item={};for(const key of ['itemCode','itemName','location','unit']){item[key]=String(r[key]??'').trim();if(!item[key])throw Error(`Row ${i+1}: ${key} is required.`);}
  const unique=item.itemCode.toLowerCase()+'|'+item.location.toLowerCase();if(seen.has(unique))throw Error(`Duplicate item and location: ${item.itemCode} / ${item.location}.`);seen.add(unique);
  for(const key of ['bookQty','unitCost']){if(String(r[key]??'').trim()==='')throw Error(`${item.itemCode}: ${key} is required.`);item[key]=Number(r[key]);if(!Number.isFinite(item[key])||item[key]<0||item[key]>1e12)throw Error(`${item.itemCode}: ${key} must be zero or a positive number.`);}
  const counted=String(r.physicalQty??'').trim()!=='';
  item.physicalQty=counted?Number(r.physicalQty):null;
  if(counted&&(!Number.isFinite(item.physicalQty)||item.physicalQty<0||item.physicalQty>1e12))throw Error(`${item.itemCode}: physical count must be zero or a positive number.`);
  const raw=counted?item.physicalQty-item.bookQty:null;
  item.variance=raw===null?null:Math.abs(raw)<1e-9?0:raw;
  item.valueVariance=item.variance===null?null:item.variance*item.unitCost;
  item.status=!counted?'Pending count':item.variance<0?'Shortage':item.variance>0?'Excess':'Matched';return item;
 });
 const counted=rows.filter(r=>r.physicalQty!==null),matched=counted.filter(r=>r.variance===0).length;
 return {rows,total:rows.length,counted:counted.length,matched,accuracy:counted.length?100*matched/counted.length:null,shortageValue:rows.reduce((a,r)=>a+Math.max(0,-(r.valueVariance??0)),0),excessValue:rows.reduce((a,r)=>a+Math.max(0,r.valueVariance??0),0)};
}
function adjust(items,index,reason,actor,time=new Date().toISOString()){
 const result=evaluate(items),row=result.rows[index];
 if(!row||row.physicalQty===null||row.variance===0)throw Error('Select a counted item with a shortage or excess.');
 if(!String(reason).trim()||!String(actor).trim())throw Error('Enter the adjustment reason and recorded-by name.');
 const updated=items.map(r=>({...r}));updated[index].bookQty=row.physicalQty;
 return {items:updated,event:{time,itemCode:row.itemCode,itemName:row.itemName,location:row.location,unit:row.unit,beforeQty:row.bookQty,afterQty:row.physicalQty,variance:row.variance,valueVariance:row.valueVariance,unitCost:row.unitCost,reason:String(reason).trim(),actor:String(actor).trim()}};
}
function parseCSV(text){text=text.replace(/^\uFEFF/,'');let rows=[],row=[],cell='',quoted=false;for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++;}else if(quoted)quoted=false;else if(cell==='')quoted=true;else throw Error('Invalid quote in CSV.');}else if(c===','&&!quoted){row.push(cell);cell='';}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(v=>v.trim()))rows.push(row);row=[];cell='';}else cell+=c;}if(quoted)throw Error('Unclosed CSV quote.');row.push(cell);if(row.some(v=>v.trim()))rows.push(row);if(!rows.length||rows[0].map(s=>s.trim()).join(',')!==headers.join(','))throw Error('Use the CSV template headers in the same order.');if(rows.length<2||rows.length>501)throw Error('Import between 1 and 500 items.');return rows.slice(1).map((r,i)=>{if(r.length!==7)throw Error(`Row ${i+2}: expected 7 columns.`);return Object.fromEntries(headers.map((h,j)=>[h,r[j].trim()]));});}
function csv(rows,keys){return keys.join(',')+'\r\n'+rows.map(r=>keys.map(k=>{let s=String(r[k]??'');if(typeof r[k]==='string'&&/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';}).join(',')).join('\r\n');}
const api={evaluate,adjust,parseCSV,csv,headers};if(typeof module!=='undefined')module.exports=api;else root.StockAudit=api;
})(typeof globalThis!=='undefined'?globalThis:this);
