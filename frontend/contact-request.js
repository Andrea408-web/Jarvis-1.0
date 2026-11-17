/* Communication commands prepare a review; they never send by themselves. */
'use strict';
window.JarvisContactRequest=text=>{
 if(typeof text!=='string')return null;
 const full=text.trim(),heard=full.slice(0,500),t=full.replace(/^(?:jarvis|astra|aeris|aether|iris)[, :]+/i,'').replace(/^bitte\s+/i,'');
 const voice=/\b(?:sprachnachricht(?:en)?|audio[- ]?nachricht(?:en)?|sprachaufnahme)\b/i.test(t)&&/^(?:schreib(?:e)?|schick(?:e)?|sende|verfasse|erstelle|mach|nimm|öffne|zeig|wie|sprachnachricht(?:en)?|audio[- ]?nachricht(?:en)?)\b/i.test(t);
 let kind;
 if(voice)kind='mail';
 else if(/^(?:ruf(?:e)?\s+.+\s+an[.!?]*|wähl(?:e)?\s+.+)$/i.test(t))kind='call';
 else if(/^(?:schreib(?:e)?|schick(?:e)?|sende|verfasse)\b/i.test(t)){if(/\b(?:e-?mail|mail)\b/i.test(t))kind='mail';else if(/\b(?:sms|nachricht)\b/i.test(t))kind='sms';}
 if(!kind)return null;
 const body=t.match(/(?:mit (?:dem )?(?:text|inhalt)\s*:?|\btext\s*:)\s*([\s\S]+)$/i)||t.match(/:\s+([\s\S]+)$/);
 const addressPart=t.split(/\s+mit (?:dem )?(?:text|inhalt)\b|:\s*/i)[0];
 const target=addressPart.match(/\b(?:sprachnachricht(?:en)?|audio[- ]?nachricht(?:en)?|e-?mail|mail|sms|nachricht)\s+(?:an|für)\s+(.+)$/i)||addressPart.match(/^(?:schreib(?:e)?|schick(?:e)?|sende)\s+(.+?)\s+(?:eine? |die )?(?:sprachnachricht|audio[- ]?nachricht|e-?mail|mail|sms|nachricht)\b/i);
 return {kind,heard,recipient:target?target[1].trim().replace(/[.!?]$/,''):'',text:body&&kind!=='call'?body[1].slice(0,8001):'',...(voice?{voice:true,voicePreset:/\b(?:thorsten|deiner stimme|jarvis[- ]stimme)\b/i.test(t)?'thorsten':'own'}:{})};
};
