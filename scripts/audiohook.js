(()=>{const AC=window.AudioContext;const contexts=[];
window.AudioContext=window.webkitAudioContext=class extends AC{constructor(...a){super(...a);this.__rec=this.createMediaStreamDestination();contexts.push(this);window.__ctx=this;}};
const orig=AudioNode.prototype.connect;
AudioNode.prototype.connect=function(dest,...rest){const r=orig.call(this,dest,...rest);try{if(dest&&dest instanceof AudioDestinationNode&&this.context.__rec)orig.call(this,this.context.__rec);}catch(e){}return r;};
window.__startRec=()=>{const c=window.__ctx;if(!c)return 'noctx';const mr=new MediaRecorder(c.__rec.stream,{mimeType:'audio/webm;codecs=opus',audioBitsPerSecond:192000});window.__chunks=[];mr.ondataavailable=e=>window.__chunks.push(e.data);mr.start(1000);window.__mr=mr;window.__recStart=Date.now();return window.__recStart;};
window.__stopRec=()=>new Promise(res=>{const mr=window.__mr;mr.onstop=async()=>{const blob=new Blob(window.__chunks,{type:'audio/webm'});const buf=new Uint8Array(await blob.arrayBuffer());let s='';for(let i=0;i<buf.length;i+=32768)s+=String.fromCharCode.apply(null,buf.subarray(i,i+32768));res(btoa(s));};mr.stop();});
})();
