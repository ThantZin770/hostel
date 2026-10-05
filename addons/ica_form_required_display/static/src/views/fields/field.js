import {Field} from "@web/views/fields/field";
import {patch} from "@web/core/utils/patch";
import {fieldVisualFeedback} from "@web/views/fields/field";

patch(Field.prototype, {
    get classNames() {
        let classNames= super.classNames;
        const { class: _class, fieldInfo, name, record } = this.props;
        const { readonly, required, invalid, empty } = fieldVisualFeedback(
            this.field,
            record,
            name,
            fieldInfo || {}
        );
        if(required || invalid){
            classNames['o_field_invalid']=true;
        }

        return classNames;
    }
});