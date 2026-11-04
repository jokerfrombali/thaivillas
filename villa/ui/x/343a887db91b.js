(function(){
  var WA='66811237388';

  function villaName(){
    var t=(document.title||'').split('|')[0].trim();
    if(t)return t;
    var h=document.querySelector('h1');
    return h?h.textContent.trim():'this villa';
  }
  function villaUrl(){
    var c=document.querySelector('link[rel="canonical"]');
    if(c&&c.href)return c.href.split('?')[0];
    return location.origin+location.pathname;
  }
  function fmt(d){
    try{return d.toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short',year:'numeric'});}
    catch(e){return d.toDateString();}
  }
  function picked(){
    try{return (window.thbGetDates&&window.thbGetDates())||{};}catch(e){return {};}
  }
  function guests(){
    try{var g=window.thbGetGuests&&window.thbGetGuests();return g&&g.count?g.count:0;}catch(e){return 0;}
  }
  /* '' until both dates are picked */
  function details(){
    var d=picked();
    if(!d.start||!d.end)return '';
    var n=Math.round((d.end-d.start)/86400000),g=guests();
    var s='\nCheck-in: '+fmt(d.start)+'\nCheck-out: '+fmt(d.end)+'\nNights: '+n;
    if(g)s+='\nGuests: '+g;
    return s;
  }
  function message(){
    return 'Hi Luxury Phuket! Availability request for '+villaName()+'.'+details()+'\nLink: '+villaUrl();
  }

  /* every WhatsApp booking link carries the current dates at all times */
  function syncOne(a){
    var u;try{u=new URL(a.href,location.href);}catch(e){return;}
    var t=a.getAttribute('data-thb-watext');
    if(t===null){
      t=(u.searchParams.get('text')||'').replace(/\s*(?:Dates:|Check-in:)\s*[\s\S]*$/,'');
      a.setAttribute('data-thb-watext',t);
    }
    if(!t||!/book|availab/i.test(t))return;
    var extra=details();
    u.searchParams.set('text',extra?t+extra:t);
    a.href=u.toString();
  }
  function sync(){[].forEach.call(document.querySelectorAll('a[href*="wa.me"]'),syncOne);}

  function askForDates(){
    var sec=document.getElementById('section-availability');
    if(!sec)return;
    var nav=document.getElementById('thbSecNav');
    var off=72+(nav&&nav.classList.contains('is-on')?nav.offsetHeight:0)+14;
    var y=sec.getBoundingClientRect().top+window.pageYOffset-off;
    try{window.scrollTo({top:Math.max(0,y),behavior:'smooth'});}catch(e){window.scrollTo(0,Math.max(0,y));}
    var label=document.getElementById('selectedDateRange');
    if(label){
      label.textContent=picked().start?'Now pick your check-out date':'Please pick your check-in and check-out dates';
      label.classList.add('thb-need-dates');
    }
    sec.classList.remove('thb-nudge');
    setTimeout(function(){sec.classList.add('thb-nudge');},280);
    setTimeout(function(){sec.classList.remove('thb-nudge');},1300);
  }

  function fire(e){
    e.preventDefault();
    if(!details()){askForDates();return;}
    var url='https://wa.me/'+WA+'?text='+encodeURIComponent(message());
    var w=window.open(url,'_blank','noopener');
    if(!w)location.href=url;
  }

  /* header CTA + the booking card buttons that did nothing before */
  var ctas=[].slice.call(document.querySelectorAll('[data-thb-cta="check-availability"]'));
  [].forEach.call(document.querySelectorAll('#property-booking button'),function(b){
    if(/^(request to book|add dates|reserve)$/i.test((b.textContent||'').trim()))ctas.push(b);
  });
  ctas.forEach(function(el){el.addEventListener('click',fire);});

  /* the card's date fields open the real calendar instead of nothing */
  [].forEach.call(document.querySelectorAll('[data-testid="booking-calendar-trigger"]'),function(el){
    el.addEventListener('click',function(e){e.preventDefault();askForDates();});
  });

  /* re-sync whenever the selection or the guest count changes */
  var label=document.getElementById('selectedDateRange');
  if(label&&window.MutationObserver){
    new MutationObserver(sync).observe(label,{childList:true,characterData:true,subtree:true});
  }
  document.addEventListener('click',function(e){
    var t=e.target;
    if(t.closest&&t.closest('.calendar-day')){
      var l=document.getElementById('selectedDateRange');
      if(l)l.classList.remove('thb-need-dates');
      requestAnimationFrame(sync);
    }
    if(t.id==='guestPlus'||t.id==='guestMinus')requestAnimationFrame(sync);
    var a=t.closest&&t.closest('a[href*="wa.me"]');
    if(a)syncOne(a);
  },true);

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',sync);
  else sync();
})();