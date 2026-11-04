(function(){
  var nav=document.getElementById('thbSecNav');if(!nav)return;
  var box=nav.querySelector('.tsn-in');
  var links=[].slice.call(nav.querySelectorAll('a[href^="#"]'));
  var secs=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
  var trigger=document.getElementById('section-summary');
  var active=-1,ticking=false,inline=false;

  /* wide screens: sit in the header row. narrow: own bar below it
     (the header has a backdrop-filter, so a fixed child there would be trapped) */
  function place(){
    var row=document.querySelector('.site-header .col-span-full');
    var wide=window.innerWidth>=1024&&!!row;
    if(wide&&nav.parentElement!==row){
      if(row.children[0])row.children[0].setAttribute('data-thb-headleft','');
      if(!document.getElementById('thbHBadge')){
        var b=document.createElement('a');
        b.id='thbHBadge';
        b.href='/';
        b.setAttribute('aria-label','Luxury Phuket \u2014 home');
        b.textContent='L';
        row.insertBefore(b,row.firstChild);
      }
      row.insertBefore(nav,row.children[2]||null);
      document.body.classList.add('thb-secnav-inline');
    }else if(!wide&&nav.parentElement!==document.body){
      document.body.appendChild(nav);
      document.body.classList.remove('thb-secnav-inline');
    }
    inline=document.body.classList.contains('thb-secnav-inline');
  }
  function offset(){return 72+(inline?14:nav.offsetHeight+10);}

  function apply(){
    ticking=false;
    place();
    var on=trigger?trigger.getBoundingClientRect().top<=110:window.pageYOffset>520;
    nav.classList.toggle('is-on',on);
    document.body.classList.toggle('thb-secnav-on',on);
    if(!on)return;
    var idx=0;
    for(var i=0;i<secs.length;i++){if(secs[i]&&secs[i].getBoundingClientRect().top<=offset()+40)idx=i;}
    if(idx===active)return;
    active=idx;
    links.forEach(function(a,i){
      if(i===idx){a.classList.add('is-active');a.setAttribute('aria-current','true');}
      else{a.classList.remove('is-active');a.removeAttribute('aria-current');}
    });
    var a=links[idx];
    if(a&&box&&box.scrollWidth>box.clientWidth+4){
      try{box.scrollTo({left:Math.max(0,a.offsetLeft-(box.clientWidth-a.offsetWidth)/2),behavior:'smooth'});}catch(e){}
    }
  }
  /* rAF plus a timer: a throttled rAF must not leave the nav stuck */
  function onScroll(){if(!ticking){ticking=true;requestAnimationFrame(apply);setTimeout(apply,40);}}

  links.forEach(function(a){a.addEventListener('click',function(e){
    var el=document.getElementById(a.getAttribute('href').slice(1));if(!el)return;
    e.preventDefault();
    var y=el.getBoundingClientRect().top+window.pageYOffset-offset();
    try{window.scrollTo({top:Math.max(0,y),behavior:'smooth'});}catch(err){window.scrollTo(0,Math.max(0,y));}
  });});
  addEventListener('scroll',onScroll,{passive:true});
  addEventListener('resize',onScroll);
  apply();
})();