document.addEventListener('DOMContentLoaded', function(){
    learn = this.getElementById ('learnMore');
    learn.addEventListener('click', function(e){
        document.getElementById('info').scrollIntoView({
            behavior :"smooth"
        })
    })
})