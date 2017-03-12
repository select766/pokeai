'use strict';

var selected_actions = ["0,Move,0", "1,Move,0"];

function render_field(field_obj) {
    console.log(field_obj);
    for (var player=0; player < 2; player++) {
        var party = field_obj.parties[player];
        var d_player = $(".player" + player);

        var f_poke = party.pokes[party.fighting_poke_idx];
        d_player.find(".dexno").text(f_poke.static_param.dexno);

        d_player.find(".hp").text("" + f_poke.hp + " / " + f_poke.static_param.max_hp);

        var d_moves = d_player.find(".moves");
        d_moves.empty();
        for (var move_idx = 0; move_idx < f_poke.static_param.move_ids.length; move_idx++) {
            var btn = $('<button type="button" class="action_button move'+move_idx+'" value="'+player+',Move,'+move_idx+'">');
            btn.text(f_poke.static_param.move_ids[move_idx]);
            btn.click(action_button_click);
            d_moves.append(btn);
        }

        d_player.find(".nv_condition").text(f_poke.nv_condition);
        var condition_str = "";
        if (f_poke.confusion_turn > 0) {
            condition_str += "Confusion=" + f_poke.confusion_turn + "; ";
        }
        if (f_poke.sleep_turn > 0) {
            condition_str += "Sleep=" + f_poke.sleep_turn + "; ";
        }
        if (f_poke.bad_poison) {
            condition_str += "BadPoison=" + f_poke.bad_poison_turn + "; ";
        }
        if (f_poke.reflect) {
            condition_str += "Reflect; ";
        }
        if (f_poke.move_handler) {
            condition_str += "Move=" + f_poke.move_handler + "; ";
        }
        d_player.find(".condition").text(condition_str);

        var rank_str = "";
        ["a", "b", "c", "s", "accuracy", "evasion"].forEach(function(rank_key){
            var rank_val = f_poke["rank_"+rank_key];
            if (rank_val != 0) {
                rank_str += rank_key + rank_val + " ";
            }
        });
        d_player.find(".rank").text(rank_str);
        
        var d_div_party = d_player.find(".party_pokes");
        d_div_party.empty();
        for (var poke_idx = 0; poke_idx < party.pokes.length; poke_idx++) {
            var btn = $('<button type="button" class="action_button poke'+poke_idx+'" value="'+player+',Change,'+poke_idx+'">');
            var poke = party.pokes[poke_idx];
            btn.text(poke.static_param.dexno + " HP=" + poke.hp + " / " + poke.static_param.max_hp);
            btn.click(action_button_click);
            d_div_party.append(btn);
            d_div_party.append($('<br>'));
        }
    }

    $(".phase").text(field_obj.phase);
    var log_str = "";
    for (var i = 0; i < field_obj.log.length; i++) {
        log_str += field_obj.log[i] + "\n";
    }
    var d_log = $("textarea[name='log']");
    d_log.val(log_str);
    if(d_log.length) {
       d_log.scrollTop(d_log[0].scrollHeight - d_log.height());
    }

    emphasize_selected_action();
}

function action_button_click() {
    var d_btn = $(this);
    var btn_val = d_btn.val();
    var btn_val_split = btn_val.split(',');
    selected_actions[Number(btn_val_split[0])] = btn_val;
    emphasize_selected_action();
}

function emphasize_selected_action() {
    $(".action_button").removeClass('selected_action');
    for (var i = 0; i < selected_actions.length; i++) {
        var selected_action = selected_actions[i];
        $("button[value='"+selected_action+"']").addClass('selected_action');
    }
}

$(function(){
    $("button[name='do_step']").click(do_step);
    fetch_update_field();
});

function fetch_update_field() {
    $.getJSON("/field", function(json){
        render_field(json);
    });
}

function do_step() {
    var post_data = {selected_actions: selected_actions};
    $.ajax({
        type: "post",
        url: "do_step",
        data: JSON.stringify(post_data),
        contentType: "application/json",
        dataType: "JSON",
        success: function (data) {
            fetch_update_field();
        }
    })
}
