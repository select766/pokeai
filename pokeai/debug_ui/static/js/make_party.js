'use strict';

$(function(){
    // init form

    for (var key in Dexno) {
        $("select[name='dexno']").append($('<option>').val(Dexno[key]).text(key));
    }
    for (var key in PokeType) {
        $("select[class='poke_type']").append($('<option>').val(PokeType[key]).text(key));
    }
    for (var key in MoveID) {
        $("select[name='move']").append($('<option>').val(MoveID[key]).text(key));
    }

});
