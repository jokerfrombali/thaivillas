(function(){
  var sec=document.getElementById('section-photos');if(!sec)return;
  var GALLERY=location.pathname.replace(/\/?$/,'/')+'gallery/';

  /* ---- counter follows the swipe ---- */
  var strip=sec.querySelector('.snap-x');
  var slides=strip?[].slice.call(strip.querySelectorAll('.snap-start')):[];
  var counter=null;
  [].forEach.call(sec.querySelectorAll('span'),function(s){
    if(!counter&&/^\d+\s*\/\s*\d+$/.test((s.textContent||'').trim()))counter=s;
  });
  if(strip&&slides.length>1&&counter){
    var ticking=false;
    var step=function(){
      var d=slides[1].offsetLeft-slides[0].offsetLeft;
      return d>0?d:slides[0].offsetWidth;
    };
    var paint=function(){
      ticking=false;
      var i=Math.max(0,Math.min(slides.length-1,Math.round(strip.scrollLeft/step())));
      var t=(i+1)+'/'+slides.length;
      if(counter.textContent.trim()!==t)counter.textContent=t;
    };
    strip.addEventListener('scroll',function(){if(!ticking){ticking=true;requestAnimationFrame(paint);}},{passive:true});
    addEventListener('resize',paint);
    paint();
  }

  /* ---- a photo opens the tour on that photo ---- */
  function nameOf(img){
    if(!img)return '';
    var s=img.getAttribute('src')||img.currentSrc||img.src||'';
    if(!s){
      var pic=img.closest('picture');
      var so=pic?pic.querySelector('source[srcset]'):null;
      if(so)s=(so.getAttribute('srcset')||'').split(',')[0].trim().split(' ')[0];
    }
    return s?s.split('/').pop().replace(/\.[a-z0-9]+$/i,''):'';
  }
  function openTour(img){
    var url=GALLERY+'?returnTo='+encodeURIComponent(location.pathname+location.search+location.hash);
    var n=nameOf(img);
    if(n)url+='&photo='+encodeURIComponent(n);
    location.href=url;
  }
  /* capture phase: the per-villa handlers stop propagation, so we go first */
  document.addEventListener('click',function(e){
    var t=e.target;if(!t||!t.closest)return;
    var cta=t.closest('button,a,span');
    var showAll=cta&&/show all photos/i.test(cta.textContent||'')&&(cta.textContent||'').trim().length<26;
    var zone=t.closest('#section-photos,#section-sleep');
    if(!showAll&&!zone)return;
    var img=null;
    if(!showAll){
      if(t.tagName==='IMG')img=t;
      else{
        var holder=t.closest('.snap-start')||t.closest('button,a,div[role="button"]')||t.parentElement;
        img=holder?holder.querySelector('img'):null;
      }
    }
    e.preventDefault();e.stopPropagation();
    if(e.stopImmediatePropagation)e.stopImmediatePropagation();
    openTour(img);
  },true);
})();